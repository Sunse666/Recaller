import json
import os
import time
import uuid
from pydantic import BaseModel, Field
from fastapi import FastAPI, HTTPException, Depends, Request, UploadFile, File, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.staticfiles import StaticFiles
from starlette.middleware.base import BaseHTTPMiddleware
from sqlalchemy.orm import Session

from .database import engine, Base, SessionLocal, get_db, DATA_DIR, run_startup_migration
from .models import User, Board, Person, AuthToken, EmailVerification
from .routers import persons, accounts, groups, boards, admin
from .auth import (
    authenticate_user, revoke_token, require_admin, require_user,
    create_user, check_login_rate, validate_password_strength,
    change_user_password, verify_password, hash_password, security, get_token_from_request,
    is_account_locked, record_failed_login, clear_failed_logins,
)
from .email_utils import send_verification_code, verify_code

class LoginPayload(BaseModel):
    username: str = Field(..., min_length=1, max_length=100)
    password: str = Field(..., min_length=1, max_length=128)

class SendCodePayload(BaseModel):
    email: str = Field(..., min_length=5, max_length=200)

class EmailRegisterPayload(BaseModel):
    email: str = Field(..., min_length=5, max_length=200)
    code: str = Field(..., min_length=4, max_length=10)
    username: str = Field(..., min_length=2, max_length=50)
    password: str = Field(..., min_length=8, max_length=128)

class ChangePasswordPayload(BaseModel):
    old_password: str = Field(..., min_length=1, max_length=128)
    new_password: str = Field(..., min_length=1, max_length=128)
    code: str | None = Field(default=None, min_length=4, max_length=10)

class ChangeEmailPayload(BaseModel):
    email: str = Field(..., min_length=5, max_length=200)
    code: str = Field(..., min_length=4, max_length=10)

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
            user = User(
                uid="1",
                username=username,
                password_hash=hash_password(password),
                role="superadmin",
            )
            db.add(user)
            db.commit()
            db.refresh(user)
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
MAX_UPLOAD_BYTES = 50 * 1024 * 1024

class BodySizeLimitMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        if request.method in ("POST", "PUT"):
            content_length = request.headers.get("content-length")
            if not content_length:
                return await call_next(request)
            size = int(content_length)
            if request.url.path.startswith("/api/upload") or request.url.path.startswith("/api/auth/avatar"):
                if size > MAX_UPLOAD_BYTES:
                    return JSONResponse(
                        status_code=413,
                        content={"detail": f"上传文件过大，最大允许 {MAX_UPLOAD_BYTES // (1024*1024)}MB"},
                    )
            elif size > MAX_BODY_BYTES:
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

    input_str = payload.username.strip()
    if "@" in input_str:
        u = db.query(User).filter(User.email == input_str.lower()).first()
    else:
        u = db.query(User).filter(User.username == input_str).first()

    lookup_key = input_str if u else payload.username.strip()
    if u and is_account_locked(u.username):
        raise HTTPException(status_code=423, detail="账号已被临时锁定，请15分钟后再试")

    if not u or not verify_password(payload.password, u.password_hash):
        if u:
            record_failed_login(u.username)
        else:
            record_failed_login(lookup_key)
        raise HTTPException(status_code=401, detail="用户名或密码错误")
    if not u.enabled:
        raise HTTPException(status_code=403, detail="账号已被禁用")

    clear_failed_logins(u.username)

    from .auth import create_token as make_token
    token = make_token(db, u.uid, u.username, u.role)
    response = JSONResponse(content={
        "username": u.username,
        "uid": u.uid, "role": u.role,
    })
    response.set_cookie(
        key="token", value=token, httponly=True, samesite="strict", secure=True, max_age=86400, path="/",
    )
    return response

_SEND_IP_ATTEMPTS: dict[str, list[float]] = {}

@app.post("/api/auth/send-code")
def send_code(payload: SendCodePayload, request: Request, db: Session = Depends(get_db)):
    ip = request.client.host if request.client else "unknown"
    now = time.time()
    entries = [t for t in _SEND_IP_ATTEMPTS.get(ip, []) if now - t < 86400]
    _SEND_IP_ATTEMPTS[ip] = entries
    if len(entries) >= 10:
        raise HTTPException(status_code=429, detail="今日发送次数已达上限")
    entries.append(now)

    email = payload.email.strip().lower()
    if not "@" in email or "." not in email.split("@")[-1]:
        raise HTTPException(status_code=400, detail="邮箱格式不正确")

    if db.query(User).filter(User.email == email).first():
        return {"status": "ok", "message": "验证码已发送"}

    err = send_verification_code(db, email, "register", ip)
    if err:
        raise HTTPException(status_code=500 if "发送失败" in err else 429, detail=err)
    return {"status": "ok", "message": "验证码已发送"}

@app.post("/api/auth/send-login-code")
def send_login_code(payload: SendCodePayload, request: Request, db: Session = Depends(get_db)):
    ip = request.client.host if request.client else "unknown"
    email = payload.email.strip().lower()
    user = db.query(User).filter(User.email == email).first()
    if not user:
        return {"status": "ok", "message": "验证码已发送"}

    err = send_verification_code(db, email, "login", ip)
    if err:
        raise HTTPException(status_code=500 if "发送失败" in err else 429, detail=err)
    return {"status": "ok", "message": "验证码已发送"}

@app.post("/api/auth/login-by-code")
def login_by_code(payload: EmailRegisterPayload, request: Request, db: Session = Depends(get_db)):
    """邮箱验证码登录"""
    email = payload.email.strip().lower()
    verify_err = verify_code(db, email, payload.code, "login")
    if verify_err:
        raise HTTPException(status_code=400, detail=verify_err)

    user = db.query(User).filter(User.email == email).first()
    if not user:
        raise HTTPException(status_code=404, detail="用户不存在")
    if not user.enabled:
        raise HTTPException(status_code=403, detail="账号已被禁用")

    from .auth import create_token as make_token
    token = make_token(db, user.uid, user.username, user.role)
    response = JSONResponse(content={
        "username": user.username,
        "uid": user.uid, "role": user.role,
    })
    response.set_cookie(
        key="token", value=token, httponly=True, samesite="strict", secure=True, max_age=86400, path="/",
    )
    return response

@app.post("/api/auth/register-email")
def register_email(payload: EmailRegisterPayload, request: Request, db: Session = Depends(get_db)):
    """邮箱验证码注册"""
    email = payload.email.strip().lower()
    if not "@" in email or "." not in email.split("@")[-1]:
        raise HTTPException(status_code=400, detail="邮箱格式不正确")

    verify_err = verify_code(db, email, payload.code, "register")
    if verify_err:
        raise HTTPException(status_code=400, detail=verify_err)

    if db.query(User).filter(User.username == payload.username).first():
        raise HTTPException(status_code=409, detail="用户名已存在")
    if db.query(User).filter(User.email == email).first():
        raise HTTPException(status_code=409, detail="该邮箱已被注册")

    err = validate_password_strength(payload.password)
    if err:
        raise HTTPException(status_code=400, detail=err)

    user = create_user(db, payload.username, payload.password, role="user")
    user.email = email
    user.email_verified = True
    db.commit()
    return {"uid": user.uid, "username": payload.username, "email": email}

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
    try:
        user = create_user(db, username, password, role="user")
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

@app.post("/api/auth/send-pwd-code")
def send_pwd_code(request: Request, user: dict = Depends(require_user), db: Session = Depends(get_db)):
    u = db.query(User).filter(User.uid == user["uid"]).first()
    if not u or not u.email:
        raise HTTPException(status_code=400, detail="请先绑定邮箱")
    ip = request.client.host if request.client else "unknown"
    now = time.time()
    entries = [t for t in _SEND_IP_ATTEMPTS.get(ip, []) if now - t < 86400]
    _SEND_IP_ATTEMPTS[ip] = entries
    if len(entries) >= 10:
        raise HTTPException(status_code=429, detail="今日发送次数已达上限")
    entries.append(now)
    err = send_verification_code(db, u.email, "pwd_change", ip)
    if err:
        raise HTTPException(status_code=500 if "发送失败" in err else 429, detail=err)
    return {"status": "ok", "masked": u.email[:3] + "***" + u.email.split("@")[-1]}

@app.post("/api/auth/change-password")
def change_password(payload: ChangePasswordPayload, user: dict = Depends(require_user), db: Session = Depends(get_db)):
    u = db.query(User).filter(User.uid == user["uid"]).first()
    if u and u.email:
        if not payload.code:
            raise HTTPException(status_code=400, detail="需要邮箱验证码")
        err = verify_code(db, u.email, payload.code, "pwd_change")
        if err:
            raise HTTPException(status_code=400, detail=err)
    err = change_user_password(db, user["username"], payload.old_password, payload.new_password)
    if err:
        raise HTTPException(status_code=400, detail=err)
    return {"status": "ok"}

@app.post("/api/auth/change-email")
def change_email(payload: ChangeEmailPayload, user: dict = Depends(require_user), db: Session = Depends(get_db)):
    email = payload.email.strip().lower()
    if not "@" in email or "." not in email.split("@")[-1]:
        raise HTTPException(status_code=400, detail="邮箱格式不正确")

    err = verify_code(db, email, payload.code, "register")
    if err:
        raise HTTPException(status_code=400, detail=err)

    existing = db.query(User).filter(User.email == email).first()
    if existing:
        raise HTTPException(status_code=409, detail="该邮箱已被其他账号绑定")

    u = db.query(User).filter(User.uid == user["uid"]).first()
    if not u:
        raise HTTPException(status_code=404, detail="用户不存在")
    u.email = email
    u.email_verified = True
    db.commit()
    return {"status": "ok", "email": email}

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
    response = JSONResponse(content={"username": new_username})
    response.set_cookie(
        key="token", value=new_token, httponly=True, samesite="strict", secure=True, max_age=86400, path="/",
    )
    return response

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
    is_gif = (ext == ".gif")
    contents = _process_image(contents, ext, max_px)
    if max_size > 0 and len(contents) > max_size:
        raise HTTPException(status_code=413, detail=f"压缩后仍超过 {limits['upload_max_size_mb']}MB，请上传更小的图片")
    filename_base = uuid.uuid4().hex
    save_ext = ".gif" if is_gif else ".webp"
    filename = f"{filename_base}{save_ext}"
    user_dir = os.path.join(DATA_DIR, "uploads", user["uid"])
    os.makedirs(user_dir, exist_ok=True)
    filepath = os.path.join(user_dir, filename)
    with open(filepath, "wb") as f:
        f.write(contents)
    url = f"/uploads/{user['uid']}/{filename}"
    thumb_url = None
    medium_url = None
    if not is_gif:
        thumb_contents = _generate_thumbnail(contents)
        thumb_filename = f"{filename_base}.thumb.webp"
        thumb_filepath = os.path.join(user_dir, thumb_filename)
        with open(thumb_filepath, "wb") as f:
            f.write(thumb_contents)
        thumb_url = f"/uploads/{user['uid']}/{thumb_filename}"
        medium_contents = _generate_medium(contents)
        medium_filename = f"{filename_base}.medium.webp"
        medium_filepath = os.path.join(user_dir, medium_filename)
        with open(medium_filepath, "wb") as f:
            f.write(medium_contents)
        medium_url = f"/uploads/{user['uid']}/{medium_filename}"
    u_ = db.query(User).filter(User.uid == user["uid"]).first()
    if u_:
        u_.avatar = url
        db.commit()
    resp = {"url": url}
    if thumb_url:
        resp["thumb_url"] = thumb_url
    if medium_url:
        resp["medium_url"] = medium_url
    return resp

ALLOWED_EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp", ".gif"}
MAX_UPLOAD_SIZE = 10 * 1024 * 1024
MAX_IMAGE_PX = 2048

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
        img2.save(out, format="WEBP", quality=85)
        return out.getvalue()
    except Exception as e:
        print(f"[image] 处理失败 ({ext}): {e}，使用原始文件")
        return contents

THUMB_MAX_PX = 400
MEDIUM_MAX_PX = 1080

def _generate_thumbnail(contents: bytes) -> bytes:
    try:
        from PIL import Image
        import io
        img = Image.open(io.BytesIO(contents))
        w, h = img.size
        if w > THUMB_MAX_PX or h > THUMB_MAX_PX:
            ratio = THUMB_MAX_PX / max(w, h)
            img = img.resize((int(w * ratio), int(h * ratio)), Image.LANCZOS)
        out = io.BytesIO()
        img.save(out, format="WEBP", quality=80)
        return out.getvalue()
    except Exception as e:
        print(f"[image] 缩略图生成失败: {e}")
        return contents

def _generate_medium(contents: bytes) -> bytes:
    try:
        from PIL import Image
        import io
        img = Image.open(io.BytesIO(contents))
        w, h = img.size
        if w > MEDIUM_MAX_PX or h > MEDIUM_MAX_PX:
            ratio = MEDIUM_MAX_PX / max(w, h)
            img = img.resize((int(w * ratio), int(h * ratio)), Image.LANCZOS)
        out = io.BytesIO()
        img.save(out, format="WEBP", quality=85)
        return out.getvalue()
    except Exception as e:
        print(f"[image] 压缩图生成失败: {e}")
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
    is_gif = (ext == ".gif")
    filename_base = uuid.uuid4().hex
    save_ext = ".gif" if is_gif else ".webp"
    filename = f"{filename_base}{save_ext}"
    user_dir = os.path.join(DATA_DIR, "uploads", user["uid"])
    os.makedirs(user_dir, exist_ok=True)
    filepath = os.path.join(user_dir, filename)
    with open(filepath, "wb") as f:
        f.write(contents)
    url = f"/uploads/{user['uid']}/{filename}"
    thumb_url = None
    medium_url = None
    if not is_gif:
        thumb_contents = _generate_thumbnail(contents)
        thumb_filename = f"{filename_base}.thumb.webp"
        thumb_filepath = os.path.join(user_dir, thumb_filename)
        with open(thumb_filepath, "wb") as f:
            f.write(thumb_contents)
        thumb_url = f"/uploads/{user['uid']}/{thumb_filename}"
        medium_contents = _generate_medium(contents)
        medium_filename = f"{filename_base}.medium.webp"
        medium_filepath = os.path.join(user_dir, medium_filename)
        with open(medium_filepath, "wb") as f:
            f.write(medium_contents)
        medium_url = f"/uploads/{user['uid']}/{medium_filename}"
    resp = {"url": url}
    if thumb_url:
        resp["thumb_url"] = thumb_url
    if medium_url:
        resp["medium_url"] = medium_url
    return resp

@app.get("/api/images")
def list_uploaded_images(
    user: dict = Depends(require_user),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=50, ge=1, le=200),
):
    """List files in the user's upload directory with pagination (scans disk)."""
    user_dir = os.path.join(DATA_DIR, "uploads", user["uid"])
    if not os.path.isdir(user_dir):
        return {"items": [], "total": 0, "page": page, "page_size": page_size}
    result = []
    for fname in os.listdir(user_dir):
        fpath = os.path.join(user_dir, fname)
        if not os.path.isfile(fpath):
            continue
        if fname.endswith(".thumb.webp") or fname.endswith(".medium.webp"):
            continue
        url = f"/uploads/{user['uid']}/{fname}"
        stat = os.stat(fpath)
        result.append({"url": url, "size": stat.st_size, "mtime": stat.st_mtime})
    result.sort(key=lambda x: x["mtime"], reverse=True)
    total = len(result)
    start = (page - 1) * page_size
    end = start + page_size
    return {
        "items": result[start:end],
        "total": total,
        "page": page,
        "page_size": page_size,
    }

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
                "random_order": bool(b.random_order),
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
