import os
import time
import uuid
from fastapi import FastAPI, HTTPException, Depends, Request, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.staticfiles import StaticFiles
from starlette.middleware.base import BaseHTTPMiddleware
from sqlalchemy.orm import Session

from .database import engine, Base, SessionLocal, get_db, DATA_DIR, run_startup_migration
from .models import User, Board, Person, AuthToken
from .routers import persons, accounts, groups, boards
from .auth import (
    authenticate_user, revoke_token, require_admin, require_user,
    create_user, check_login_rate, validate_password_strength,
    change_user_password, security, get_token_from_request,
)
from .models import User

Base.metadata.create_all(bind=engine)


def _init_admin():
    db = SessionLocal()
    try:
        if db.query(User).count() == 0:
            username = os.environ.get("ADMIN_USER", "admin")
            password = os.environ.get("ADMIN_PASS", "admin123")
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

_init_admin()
run_startup_migration()
_cleanup_expired_tokens()

app = FastAPI(title="群友记忆助手 API")

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
        if request.method in ("POST", "PUT") and not request.url.path.startswith("/api/upload"):
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
        response.headers["Content-Security-Policy"] = "default-src 'self'; script-src 'self'; style-src 'self' 'unsafe-inline'; img-src 'self' data: blob:"
        return response

app.add_middleware(SecurityHeadersMiddleware)

@app.post("/api/auth/login")
def login(payload: dict, request: Request, db: Session = Depends(get_db)):
    client_ip = request.client.host if request.client else "unknown"
    if not check_login_rate(client_ip):
        raise HTTPException(status_code=429, detail="登录尝试过于频繁，请稍后再试")
    result = authenticate_user(db, payload.get("username", ""), payload.get("password", ""))
    if not result:
        raise HTTPException(status_code=401, detail="用户名或密码错误")
    response = JSONResponse(content={
        "token": result["token"], "username": result["username"],
        "uid": result["uid"], "role": result["role"],
    })
    response.set_cookie(
        key="token", value=result["token"], httponly=True, samesite="lax", max_age=86400, path="/",
    )
    return response

@app.post("/api/auth/register")
def register(payload: dict, request: Request, db: Session = Depends(get_db)):
    client_ip = request.client.host if request.client else "unknown"
    if not check_login_rate(client_ip):
        raise HTTPException(status_code=429, detail="操作过于频繁，请稍后再试")
    username = payload.get("username", "")
    password = payload.get("password", "")
    err = validate_password_strength(password)
    if err:
        raise HTTPException(status_code=400, detail=err)
    from .models import Board
    try:
        user = create_user(db, username, password, role="user")
        board = Board(
            user_id=user.id, name="默认看板", icon="👥",
            card_label="群友", cards_label="群友们",
            group_label="群", groups_label="群组",
            field_config="{}", is_public=False, sort_order=0,
        )
        db.add(board)
        db.commit()
        return {"uid": user.uid, "username": username}
    except ValueError as e:
        raise HTTPException(status_code=409, detail=str(e))

@app.post("/api/auth/logout")
def logout(request: Request, creds: HTTPAuthorizationCredentials | None = Depends(security)):
    token = get_token_from_request(request)
    if token:
        revoke_token(token)
    response = JSONResponse(content={"status": "ok"})
    response.delete_cookie("token", path="/")
    return response

@app.get("/api/auth/me")
def me(user: dict = Depends(require_user)):
    return user

@app.post("/api/auth/change-password")
def change_password(payload: dict, user: dict = Depends(require_user), db: Session = Depends(get_db)):
    old_password = payload.get("old_password", "")
    new_password = payload.get("new_password", "")
    if not old_password or not new_password:
        raise HTTPException(status_code=400, detail="请提供原密码和新密码")
    err = change_user_password(db, user["username"], old_password, new_password)
    if err:
        raise HTTPException(status_code=400, detail=err)
    return {"status": "ok"}

ALLOWED_EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp", ".gif"}
MAX_UPLOAD_SIZE = 10 * 1024 * 1024

@app.post("/api/upload")
async def upload_file(file: UploadFile = File(...), user: dict = Depends(require_user)):
    ext = os.path.splitext(file.filename or "")[1].lower()
    if ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(status_code=400, detail=f"不支持的文件格式: {ext}")
    contents = await file.read()
    if len(contents) > MAX_UPLOAD_SIZE:
        raise HTTPException(status_code=413, detail="文件过大，最大允许 10MB")
    user_dir = os.path.join(DATA_DIR, "uploads", user["uid"])
    os.makedirs(user_dir, exist_ok=True)
    filename = f"{uuid.uuid4().hex}{ext}"
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
        "boards": [
            {
                "id": b.id, "name": b.name, "icon": b.icon,
                "description": b.description, "card_label": b.card_label,
                "cards_label": b.cards_label,
                "cards_count": db.query(Person).filter(Person.board_id == b.id).count(),
            }
            for b in public_boards
        ],
    }

app.include_router(persons.router)
app.include_router(accounts.router)
app.include_router(groups.router)
app.include_router(boards.router)

uploads_path = os.path.join(DATA_DIR, "uploads")
os.makedirs(uploads_path, exist_ok=True)
app.mount("/uploads", StaticFiles(directory=uploads_path), name="uploads")

@app.get("/api/health")
def health():
    return {"status": "ok"}
