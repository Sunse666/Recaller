import json
import os
import time
import uuid
from pydantic import BaseModel, Field
from fastapi import FastAPI, HTTPException, Depends, Request, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.staticfiles import StaticFiles
from starlette.middleware.base import BaseHTTPMiddleware
from sqlalchemy.orm import Session

from .database import engine, Base, SessionLocal, get_db, DATA_DIR, run_startup_migration
from .models import User, Board, Person, AuthToken
from .routers import persons, accounts, groups, boards, admin
from .auth import (
    authenticate_user, revoke_token, require_admin, require_user,
    create_user, check_login_rate, validate_password_strength,
    change_user_password, security, get_token_from_request,
)

class LoginPayload(BaseModel):
    username: str = Field(..., min_length=1, max_length=100)
    password: str = Field(..., min_length=1, max_length=128)

class ChangePasswordPayload(BaseModel):
    old_password: str = Field(..., min_length=1, max_length=128)
    new_password: str = Field(..., min_length=1, max_length=128)

class ChangeUsernamePayload(BaseModel):
    username: str = Field(..., min_length=2, max_length=50)

Base.metadata.create_all(bind=engine)

def _init_admin():
    db = SessionLocal()
    try:
        if db.query(User).count() == 0:
            username = os.environ.get("ADMIN_USER") or "admin"
            password = os.environ.get("ADMIN_PASS") or "admin123"
            if not os.environ.get("ADMIN_PASS"):
                print("[init] 警告: 未设置 ADMIN_PASS 环境变量，使用默认密码 admin123。生产环境请务必修改！")
            err = validate_password_strength(password)
            if err:
                print(f"[init] 警告: 默认管理员密码强度不足: {err}")
            user = create_user(db, username, password, role="admin")
            print(f"[init] 已创建管理员: {username} (uid={user.uid})")
    finally:
        db.close()

def _cleanup_expired_tokens():
    import datetime as _dt
    db = SessionLocal()
    try:
        db.query(AuthToken).filter(AuthToken.expires_at < _dt.datetime.now(_dt.timezone.utc)).delete()
        db.commit()
    finally:
        db.close()

run_startup_migration()
_init_admin()
_cleanup_expired_tokens()

app = FastAPI(title="Recaller Gallery API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:5174", "http://localhost:5175"],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE"],
    allow_headers=["Content-Type", "Authorization"],
)

MAX_BODY_BYTES = 1 * 1024 * 1024

class BodySizeLimitMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        if request.method in ("POST", "PUT") and not request.url.path.startswith("/api/upload") and not request.url.path.startswith("/api/auth/avatar"):
            content_length = request.headers.get("content-length")
            if content_length and int(content_length) > MAX_BODY_BYTES:
                return JSONResponse(
                    status_code=413,
                    content={"detail": "请求体过大，最大允许 1MB"},
                )
        return await call_next(request)

app.add_middleware(BodySizeLimitMiddleware)

_MUTATION_ATTEMPTS: dict[str, list[float]] = {}
_MAX_MUTATIONS = 30
_MUTATION_WINDOW = 60

class MutationRateLimitMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        if request.method in ("POST", "PUT", "DELETE"):
            ip = request.client.host if request.client else "unknown"
            now = time.time()
            attempts = [t for t in _MUTATION_ATTEMPTS.get(ip, []) if now - t < _MUTATION_WINDOW]
            _MUTATION_ATTEMPTS[ip] = attempts
            if len(attempts) >= _MAX_MUTATIONS:
                return JSONResponse(status_code=429, content={"detail": "操作过于频繁，请稍后再试"})
            attempts.append(now)
        return await call_next(request)

app.add_middleware(MutationRateLimitMiddleware)

class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        response = await call_next(request)
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        response.headers["Cache-Control"] = "no-store"
        response.headers["Content-Security-Policy"] = "default-src 'self'; script-src 'self'; style-src 'self'; img-src 'self' data: blob:"
        return response

app.add_middleware(SecurityHeadersMiddleware)

@app.post("/api/auth/login")
def login(payload: LoginPayload, request: Request, db: Session = Depends(get_db)):
    client_ip = request.client.host if request.client else "unknown"
    if not check_login_rate(client_ip):
        raise HTTPException(status_code=429, detail="登录尝试过于频繁，请稍后再试")
    result = authenticate_user(db, payload.username, payload.password)
    if not result:
        raise HTTPException(status_code=401, detail="用户名或密码错误")
    u = db.query(User).filter(User.username == payload.username).first()
    if u and not u.enabled:
        raise HTTPException(status_code=403, detail="账号已被禁用")
    response = JSONResponse(content={
        "token": result["token"], "username": result["username"],
        "uid": result["uid"], "role": result["role"],
    })
    response.set_cookie(
        key="token", value=result["token"], httponly=True, samesite="lax", max_age=86400, path="/",
    )
    return response

@app.post("/api/auth/register")
def register(payload: LoginPayload, request: Request, db: Session = Depends(get_db)):
    client_ip = request.client.host if request.client else "unknown"
    if not check_login_rate(client_ip):
        raise HTTPException(status_code=429, detail="操作过于频繁，请稍后再试")
    username = payload.username
    password = payload.password
    err = validate_password_strength(password)
    if err:
        raise HTTPException(status_code=400, detail=err)
    from .models import Board
    try:
        user = create_user(db, username, password, role="user")
        board = Board(
            user_id=user.id, name="默认画板", icon="🖼️",
            card_label="图片", cards_label="图片",
            group_label="图组", groups_label="图组",
            board_type="image",
            field_config="{}", is_public=False, sort_order=0,
        )
        db.add(board)
        db.commit()
        return {"uid": user.uid, "username": username}
    except ValueError:
        raise HTTPException(status_code=409, detail="注册失败，请重试")

@app.post("/api/auth/logout")
def logout(request: Request, creds: HTTPAuthorizationCredentials | None = Depends(security)):
    token = get_token_from_request(request)
    if token:
        revoke_token(token)
    response = JSONResponse(content={"status": "ok"})
    response.delete_cookie("token", path="/")
    return response

@app.get("/api/auth/me")
def me(user: dict = Depends(require_user), db: Session = Depends(get_db)):
    u = db.query(User).filter(User.uid == user["uid"]).first()
    return {
        "uid": user["uid"],
        "username": user["username"],
        "role": user["role"],
        "avatar": u.avatar if u else None,
    }

@app.post("/api/auth/change-password")
def change_password(payload: ChangePasswordPayload, user: dict = Depends(require_user), db: Session = Depends(get_db)):
    err = change_user_password(db, user["username"], payload.old_password, payload.new_password)
    if err:
        raise HTTPException(status_code=400, detail=err)
    return {"status": "ok"}

@app.post("/api/auth/change-username")
def change_username(payload: ChangeUsernamePayload, user: dict = Depends(require_user), db: Session = Depends(get_db)):
    new_username = payload.username.strip()
    if len(new_username) < 2 or len(new_username) > 50:
        raise HTTPException(status_code=400, detail="用户名长度需要 2-50 个字符")
    existing = db.query(User).filter(User.username == new_username).first()
    if existing:
        raise HTTPException(status_code=409, detail="用户名已被占用")
    u = db.query(User).filter(User.uid == user["uid"]).first()
    if not u:
        raise HTTPException(status_code=404, detail="用户不存在")
    old = u.username
    u.username = new_username
    from .auth import revoke_user_tokens, create_token
    revoke_user_tokens(old)
    db.commit()
    new_token = create_token(db, u.uid, new_username, u.role)
    return {"username": new_username, "token": new_token}

_AVATAR_ATTEMPTS: dict[str, list[float]] = {}
_MAX_AVATAR_PER_MIN = 5

@app.post("/api/auth/avatar")
async def upload_avatar(request: Request, file: UploadFile = File(...), user: dict = Depends(require_user), db: Session = Depends(get_db)):
    ip = request.client.host if request.client else "unknown"
    now = time.time()
    attempts = [t for t in _AVATAR_ATTEMPTS.get(ip, []) if now - t < 60]
    _AVATAR_ATTEMPTS[ip] = attempts
    if len(attempts) >= _MAX_AVATAR_PER_MIN:
        raise HTTPException(status_code=429, detail="上传过于频繁，请稍后再试")
    attempts.append(now)
    limits = _get_effective_limits(user["uid"])
    max_size = limits["upload_max_size_mb"] * 1024 * 1024
    if max_size == 0:
        max_size = 100 * 1024 * 1024
    max_px = limits["upload_max_px"]
    ext = os.path.splitext(file.filename or "")[1].lower()
    if ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(status_code=400, detail=f"不支持的文件格式: {ext}")
    contents = await file.read()
    if max_size > 0 and len(contents) > max_size * 2:
        raise HTTPException(status_code=413, detail=f"文件过大，最大允许 {limits['upload_max_size_mb']}MB（压缩前）")
    contents = _process_image(contents, ext, max_px)
    if max_size > 0 and len(contents) > max_size:
        raise HTTPException(status_code=413, detail=f"压缩后仍超过 {limits['upload_max_size_mb']}MB，请上传更小的图片")
    filename = f"{uuid.uuid4().hex}{ext}"
    user_dir = os.path.join(DATA_DIR, "uploads", user["uid"])
    os.makedirs(user_dir, exist_ok=True)
    filepath = os.path.join(user_dir, filename)
    with open(filepath, "wb") as f:
        f.write(contents)
    url = f"/uploads/{user['uid']}/{filename}"
    u_ = db.query(User).filter(User.uid == user["uid"]).first()
    if u_:
        u_.avatar = url
        db.commit()
    return {"url": url}

ALLOWED_EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp", ".gif"}
MAX_UPLOAD_SIZE = 10 * 1024 * 1024
MAX_IMAGE_PX = 2048
JPEG_QUALITY = 85


def _get_effective_limits(user_uid: str) -> dict:
    defaults = {
        "upload_rate_per_min": 10,
        "upload_max_size_mb": 10,
        "upload_max_px": 2048,
    }
    db = SessionLocal()
    try:
        u = db.query(User).filter(User.uid == user_uid).first()
        if u and u.limits:
            user_limits = json.loads(u.limits)
            for k in defaults:
                if k in user_limits:
                    defaults[k] = user_limits[k]
    finally:
        db.close()
    return defaults

def _process_image(contents: bytes, ext: str, max_px: int = MAX_IMAGE_PX) -> bytes:
    if ext == ".gif":
        return contents
    try:
        from PIL import Image
        import io
        img = Image.open(io.BytesIO(contents))
        img = img.convert("RGB") if img.mode in ("RGBA", "P", "LA") else img
        if max_px > 0:
            w, h = img.size
            if w > max_px or h > max_px:
                ratio = max_px / max(w, h)
                img = img.resize((int(w * ratio), int(h * ratio)), Image.LANCZOS)
        data = list(img.getdata())
        img2 = Image.new(img.mode, img.size)
        img2.putdata(data)
        out = io.BytesIO()
        fmt = "JPEG" if ext in (".jpg", ".jpeg") else ("PNG" if ext == ".png" else "WEBP")
        save_kw = {"format": fmt}
        if fmt == "JPEG":
            save_kw["quality"] = JPEG_QUALITY
            save_kw["optimize"] = True
        elif fmt == "WEBP":
            save_kw["quality"] = 85
        img2.save(out, **save_kw)
        result = out.getvalue()
        if len(result) > MAX_UPLOAD_SIZE and fmt == "JPEG":
            out2 = io.BytesIO()
            img2.save(out2, format="JPEG", quality=60, optimize=True)
            result = out2.getvalue()
        return result
    except Exception as e:
        print(f"[image] EXIF 清除/压缩失败 ({ext}): {e}，使用原始文件")
        return contents

_UPLOAD_ATTEMPTS: dict[str, list[float]] = {}
_MAX_UPLOADS_PER_MIN = 10

@app.post("/api/upload")
async def upload_file(file: UploadFile = File(...), user: dict = Depends(require_user)):
    limits = _get_effective_limits(user["uid"])
    max_rate = limits["upload_rate_per_min"]
    if max_rate > 0:
        ip = file.headers.get("x-forwarded-for", "unknown")
        now = time.time()
        attempts = [t for t in _UPLOAD_ATTEMPTS.get(ip, []) if now - t < 60]
        _UPLOAD_ATTEMPTS[ip] = attempts
        if len(attempts) >= max_rate:
            raise HTTPException(status_code=429, detail="上传过于频繁，请稍后再试")
        attempts.append(now)
    max_size = limits["upload_max_size_mb"] * 1024 * 1024
    if max_size == 0:
        max_size = 100 * 1024 * 1024
    max_px = limits["upload_max_px"]
    ext = os.path.splitext(file.filename or "")[1].lower()
    if ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(status_code=400, detail=f"不支持的文件格式: {ext}")
    contents = await file.read()
    if max_size > 0 and len(contents) > max_size * 2:
        raise HTTPException(status_code=413, detail=f"文件过大，最大允许 {limits['upload_max_size_mb']}MB（压缩前）")
    contents = _process_image(contents, ext, max_px)
    if max_size > 0 and len(contents) > max_size:
        raise HTTPException(status_code=413, detail=f"压缩后仍超过 {limits['upload_max_size_mb']}MB，请上传更小的图片")
    filename = f"{uuid.uuid4().hex}{ext}"
    user_dir = os.path.join(DATA_DIR, "uploads", user["uid"])
    os.makedirs(user_dir, exist_ok=True)
    filepath = os.path.join(user_dir, filename)
    with open(filepath, "wb") as f:
        f.write(contents)
    return {"url": f"/uploads/{user['uid']}/{filename}"}

@app.get("/api/users/{uid}")
def get_user_profile(uid: str, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.uid == uid).first()
    if not user:
        raise HTTPException(status_code=404, detail="用户不存在")
    public_boards = db.query(Board).filter(Board.user_id == user.id, Board.is_public == True).order_by(Board.sort_order).all()
    import json
    return {
        "uid": user.uid,
        "username": user.username,
        "avatar": user.avatar,
        "boards": [
            {
                "id": b.id, "name": b.name, "icon": b.icon,
                "description": b.description, "card_label": b.card_label,
                "cards_label": b.cards_label,
                "group_label": b.group_label,
                "groups_label": b.groups_label,
                "board_type": b.board_type,
                "field_config": json.loads(b.field_config or "{}"),
                "cards_count": db.query(Person).filter(Person.board_id == b.id).count(),
            }
            for b in public_boards
        ],
    }

app.include_router(persons.router)
app.include_router(accounts.router)
app.include_router(groups.router)
app.include_router(boards.router)
app.include_router(admin.router)
app.include_router(admin.public_router)

uploads_path = os.path.join(DATA_DIR, "uploads")
os.makedirs(uploads_path, exist_ok=True)
app.mount("/uploads", StaticFiles(directory=uploads_path), name="uploads")

@app.get("/api/health")
def health():
    return {"status": "ok"}
