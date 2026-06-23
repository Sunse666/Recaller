import os
from fastapi import FastAPI, HTTPException, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session

from .database import engine, Base, SessionLocal, get_db
from .routers import persons, accounts, groups
from .auth import authenticate_admin, revoke_token, verify_token, create_admin_user
from .models import AdminUser

Base.metadata.create_all(bind=engine)

app = FastAPI(title="群友记忆助手 API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:5174", "http://localhost:5175"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

security = HTTPBearer(auto_error=False)


def require_admin(
    creds: HTTPAuthorizationCredentials | None = Depends(security),
) -> str:
    if not creds or not verify_token(creds.credentials):
        raise HTTPException(status_code=401, detail="未登录或令牌已过期")
    return verify_token(creds.credentials)


# ── Auth routes ──

@app.post("/api/auth/login")
def login(payload: dict, db: Session = Depends(get_db)):
    token = authenticate_admin(db, payload.get("username", ""), payload.get("password", ""))
    if not token:
        raise HTTPException(status_code=401, detail="用户名或密码错误")
    return {"token": token, "username": payload.get("username")}


@app.post("/api/auth/logout")
def logout(user: str = Depends(require_admin)):
    # Token is extracted from the Authorization header context
    return {"status": "ok"}


@app.get("/api/auth/me")
def me(user: str = Depends(require_admin)):
    return {"username": user}


# ── Business routers ──

app.include_router(persons.router)
app.include_router(accounts.router)
app.include_router(groups.router)
@app.get("/api/health")
def health():
    return {"status": "ok"}


# ── Bootstrap admin ──

def _init_admin():
    db = SessionLocal()
    try:
        if db.query(AdminUser).count() == 0:
            username = os.environ.get("ADMIN_USER", "admin")
            password = os.environ.get("ADMIN_PASS", "admin123")
            create_admin_user(db, username, password)
            print(f"[init] 已创建管理员: {username}")
    finally:
        db.close()


_init_admin()
