import datetime
import re
import time
import secrets
from fastapi import HTTPException, Depends, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from passlib.context import CryptContext
from sqlalchemy.orm import Session
from .models import AdminUser

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
TOKENS: dict[str, dict] = {}

_LOGIN_ATTEMPTS: dict[str, list[float]] = {}
_MAX_LOGIN_ATTEMPTS = 5
_LOGIN_WINDOW = 60

def check_login_rate(ip: str) -> bool:
    now = time.time()
    attempts = [t for t in _LOGIN_ATTEMPTS.get(ip, []) if now - t < _LOGIN_WINDOW]
    _LOGIN_ATTEMPTS[ip] = attempts
    if len(attempts) >= _MAX_LOGIN_ATTEMPTS:
        return False
    attempts.append(now)
    return True

def hash_password(password: str) -> str:
    return pwd_context.hash(password)

def verify_password(password: str, hashed: str) -> bool:
    return pwd_context.verify(password, hashed)

def validate_password_strength(password: str) -> str | None:
    """Return error message if password is too weak, else None."""
    if len(password) < 8:
        return "密码长度不能少于8位"
    if len(password) > 128:
        return "密码长度不能超过128位"
    if not re.search(r"[A-Za-z]", password):
        return "密码必须包含至少一个字母"
    if not re.search(r"\d", password):
        return "密码必须包含至少一个数字"
    return None

def _cleanup_expired():
    now = datetime.datetime.now(datetime.timezone.utc)
    expired = [t for t, e in TOKENS.items() if e["expires_at"] < now]
    for t in expired:
        del TOKENS[t]

def create_token(username: str) -> str:
    _cleanup_expired()
    token = secrets.token_urlsafe(32)
    TOKENS[token] = {
        "username": username,
        "expires_at": datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(hours=24),
    }
    return token

def verify_token(token: str) -> str | None:
    entry = TOKENS.get(token)
    if not entry:
        return None
    if entry["expires_at"] < datetime.datetime.now(datetime.timezone.utc):
        del TOKENS[token]
        return None
    return entry["username"]

def revoke_token(token: str):
    TOKENS.pop(token, None)

def revoke_user_tokens(username: str):
    for t in [t for t, e in TOKENS.items() if e["username"] == username]:
        del TOKENS[t]

def create_admin_user(db: Session, username: str, password: str):
    existing = db.query(AdminUser).filter(AdminUser.username == username).first()
    if existing:
        raise ValueError(f"管理员 {username} 已存在")
    admin = AdminUser(username=username, password_hash=hash_password(password))
    db.add(admin)
    db.commit()

def authenticate_admin(db: Session, username: str, password: str) -> str | None:
    admin = db.query(AdminUser).filter(AdminUser.username == username).first()
    if not admin or not verify_password(password, admin.password_hash):
        return None
    return create_token(username)

def change_admin_password(db: Session, username: str, old_password: str, new_password: str) -> str | None:
    """Change admin password. Returns error message or None on success."""
    admin = db.query(AdminUser).filter(AdminUser.username == username).first()
    if not admin or not verify_password(old_password, admin.password_hash):
        return "原密码错误"
    strength_err = validate_password_strength(new_password)
    if strength_err:
        return strength_err
    admin.password_hash = hash_password(new_password)
    revoke_user_tokens(username)
    db.commit()
    return None

security = HTTPBearer(auto_error=False)

def get_token_from_request(request: Request) -> str | None:
    token = request.cookies.get("token")
    if token:
        return token
    auth = request.headers.get("Authorization", "")
    if auth.startswith("Bearer "):
        return auth[7:]
    return None


def require_admin(
    request: Request,
    creds: HTTPAuthorizationCredentials | None = Depends(security),
) -> str:
    token = get_token_from_request(request)
    if not token:
        raise HTTPException(status_code=401, detail="未登录或令牌已过期")
    username = verify_token(token)
    if not username:
        raise HTTPException(status_code=401, detail="未登录或令牌已过期")
    return username
