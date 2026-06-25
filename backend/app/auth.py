import datetime
import re
import time
import secrets
from fastapi import HTTPException, Depends, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from passlib.context import CryptContext
from sqlalchemy.orm import Session
from .models import User, AuthToken
from .database import SessionLocal

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

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
    if len(password) < 8:
        return "密码长度不能少于8位"
    if len(password) > 128:
        return "密码长度不能超过128位"
    if not re.search(r"[A-Za-z]", password):
        return "密码必须包含至少一个字母"
    if not re.search(r"\d", password):
        return "密码必须包含至少一个数字"
    return None

def _cleanup_expired(db: Session):
    now = datetime.datetime.now(datetime.timezone.utc)
    db.query(AuthToken).filter(AuthToken.expires_at < now).delete()
    db.commit()

def create_token(db: Session, uid: str, username: str, role: str) -> str:
    _cleanup_expired(db)
    token = secrets.token_urlsafe(32)
    entry = AuthToken(
        token=token,
        uid=uid,
        username=username,
        role=role,
        expires_at=datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(hours=24),
    )
    db.add(entry)
    db.commit()
    return token

def verify_token_full(token: str) -> dict | None:
    db = SessionLocal()
    try:
        now = datetime.datetime.now(datetime.timezone.utc)
        entry = db.query(AuthToken).filter(
            AuthToken.token == token,
            AuthToken.expires_at > now,
        ).first()
        if not entry:
            return None
        new_expiry = now + datetime.timedelta(hours=24)
        db.query(AuthToken).filter(AuthToken.id == entry.id).update({"expires_at": new_expiry})
        db.commit()
        return {"uid": entry.uid, "username": entry.username, "role": entry.role}
    finally:
        db.close()

def revoke_token(token: str):
    db = SessionLocal()
    try:
        db.query(AuthToken).filter(AuthToken.token == token).delete()
        db.commit()
    finally:
        db.close()

def revoke_user_tokens(username: str):
    db = SessionLocal()
    try:
        db.query(AuthToken).filter(AuthToken.username == username).delete()
        db.commit()
    finally:
        db.close()

def create_user(db: Session, username: str, password: str, role: str = "user") -> User:
    existing = db.query(User).filter(User.username == username).first()
    if existing:
        raise ValueError(f"用户名 {username} 已存在")
    user = User(
        uid="0",
        username=username,
        password_hash=hash_password(password),
        role=role,
    )
    db.add(user)
    db.flush()
    user.uid = str(user.id)
    db.commit()
    db.refresh(user)
    return user

def authenticate_user(db: Session, username: str, password: str) -> dict | None:
    u = db.query(User).filter(User.username == username).first()
    if not u or not verify_password(password, u.password_hash):
        return None
    token = create_token(db, u.uid, u.username, u.role)
    return {"token": token, "uid": u.uid, "username": u.username, "role": u.role}

def change_user_password(db: Session, username: str, old_password: str, new_password: str) -> str | None:
    u = db.query(User).filter(User.username == username).first()
    if not u or not verify_password(old_password, u.password_hash):
        return "原密码错误"
    err = validate_password_strength(new_password)
    if err:
        return err
    u.password_hash = hash_password(new_password)
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
) -> dict:
    token = get_token_from_request(request)
    if not token:
        raise HTTPException(status_code=401, detail="未登录或令牌已过期")
    entry = verify_token_full(token)
    if not entry:
        raise HTTPException(status_code=401, detail="未登录或令牌已过期")
    if entry["role"] not in ("admin", "superadmin"):
        raise HTTPException(status_code=403, detail="需要管理员权限")
    return entry


def require_superadmin(
    request: Request,
    creds: HTTPAuthorizationCredentials | None = Depends(security),
) -> dict:
    token = get_token_from_request(request)
    if not token:
        raise HTTPException(status_code=401, detail="未登录或令牌已过期")
    entry = verify_token_full(token)
    if not entry:
        raise HTTPException(status_code=401, detail="未登录或令牌已过期")
    if entry["role"] != "superadmin":
        raise HTTPException(status_code=403, detail="需要超级管理员权限")
    return entry


def require_user(
    request: Request,
    creds: HTTPAuthorizationCredentials | None = Depends(security),
) -> dict:
    token = get_token_from_request(request)
    if not token:
        raise HTTPException(status_code=401, detail="未登录或令牌已过期")
    entry = verify_token_full(token)
    if not entry:
        raise HTTPException(status_code=401, detail="未登录或令牌已过期")
    return entry

def optional_user(
    request: Request,
    creds: HTTPAuthorizationCredentials | None = Depends(security),
) -> dict | None:
    token = get_token_from_request(request)
    if not token:
        return None
    return verify_token_full(token)

def get_user_by_uid(db: Session, uid: str) -> User | None:
    from .models import User as UserModel
    return db.query(UserModel).filter(UserModel.uid == uid).first()

def require_board_owner(db: Session, board_id: int, user: dict):
    if board_id is None:
        return
    if user["role"] in ("admin", "superadmin"):
        return
    from .models import Board, User as UserModel
    u = db.query(UserModel).filter(UserModel.uid == user["uid"]).first()
    if not u:
        raise HTTPException(status_code=404, detail="用户不存在")
    board = db.query(Board).filter(Board.id == board_id, Board.user_id == u.id).first()
    if not board:
        raise HTTPException(status_code=403, detail="无权操作此画板")

def get_default_board_id(db: Session, user: dict) -> int | None:
    from .models import Board, User as UserModel
    u = db.query(UserModel).filter(UserModel.uid == user["uid"]).first()
    if not u:
        return None
    board = db.query(Board).filter(Board.user_id == u.id).order_by(Board.sort_order).first()
    return board.id if board else None

def check_board_visible(db: Session, board_id: int, user: dict | None):
    if board_id is None:
        return
    from .models import Board as B
    board = db.query(B).filter(B.id == board_id).first()
    if board and not board.is_public:
        if user is None:
            raise HTTPException(status_code=403, detail="无权访问")
        require_board_owner(db, board_id, user)

def require_person_owner(db: Session, person_id: int, user: dict):
    from .models import Person, Board, User as UserModel
    p = db.query(Person).get(person_id)
    if not p:
        raise HTTPException(status_code=404, detail="条目不存在")
    if p.board_id is None:
        return p
    if user["role"] in ("admin", "superadmin"):
        return p
    u = db.query(UserModel).filter(UserModel.uid == user["uid"]).first()
    if not u:
        raise HTTPException(status_code=404, detail="用户不存在")
    board = db.query(Board).filter(Board.id == p.board_id, Board.user_id == u.id).first()
    if not board:
        raise HTTPException(status_code=403, detail="无权操作此画板")
    return p
