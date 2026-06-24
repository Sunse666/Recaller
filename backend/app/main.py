import os
import time
from fastapi import FastAPI, HTTPException, Depends, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from starlette.middleware.base import BaseHTTPMiddleware
from sqlalchemy.orm import Session

from .database import engine, Base, SessionLocal, get_db
from .routers import persons, accounts, groups
from .auth import (
    authenticate_admin, revoke_token, verify_token, require_admin,
    create_admin_user, check_login_rate, validate_password_strength,
    change_admin_password, security, get_token_from_request,
)
from .models import AdminUser

Base.metadata.create_all(bind=engine)

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
        if request.method in ("POST", "PUT"):
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
    username = payload.get("username", "")
    token = authenticate_admin(db, username, payload.get("password", ""))
    if not token:
        raise HTTPException(status_code=401, detail="用户名或密码错误")
    response = JSONResponse(content={"token": token, "username": username})
    response.set_cookie(
        key="token",
        value=token,
        httponly=True,
        samesite="lax",
        max_age=86400,
        path="/",
    )
    return response

@app.post("/api/auth/logout")
def logout(request: Request, creds: HTTPAuthorizationCredentials | None = Depends(security)):
    token = get_token_from_request(request)
    if token:
        revoke_token(token)
    response = JSONResponse(content={"status": "ok"})
    response.delete_cookie("token", path="/")
    return response

@app.get("/api/auth/me")
def me(user: str = Depends(require_admin)):
    return {"username": user}

@app.post("/api/auth/change-password")
def change_password(payload: dict, user: str = Depends(require_admin), db: Session = Depends(get_db)):
    old_password = payload.get("old_password", "")
    new_password = payload.get("new_password", "")
    if not old_password or not new_password:
        raise HTTPException(status_code=400, detail="请提供原密码和新密码")
    err = change_admin_password(db, user, old_password, new_password)
    if err:
        raise HTTPException(status_code=400, detail=err)
    return {"status": "ok"}

app.include_router(persons.router)
app.include_router(accounts.router)
app.include_router(groups.router)

@app.get("/api/health")
def health():
    return {"status": "ok"}

def _init_admin():
    db = SessionLocal()
    try:
        if db.query(AdminUser).count() == 0:
            username = os.environ.get("ADMIN_USER", "admin")
            password = os.environ.get("ADMIN_PASS", "admin123")
            strength_err = validate_password_strength(password)
            if strength_err:
                print(f"[init] 警告: 默认管理员密码强度不足: {strength_err}")
            create_admin_user(db, username, password)
            print(f"[init] 已创建管理员: {username}")
    finally:
        db.close()

_init_admin()
