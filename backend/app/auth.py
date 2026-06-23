import datetime
import secrets
from passlib.context import CryptContext
from sqlalchemy.orm import Session
from .models import AdminUser

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
TOKENS = {}  # token -> {"username": str, "expires_at": datetime}


def hash_password(password: str) -> str:
    return pwd_context.hash(password)


def verify_password(password: str, hashed: str) -> bool:
    return pwd_context.verify(password, hashed)


def create_token(username: str) -> str:
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
