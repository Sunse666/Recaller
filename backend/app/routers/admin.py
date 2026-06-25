import os
import json
import shutil
import secrets
import string
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from pydantic import BaseModel, Field
from typing import Optional, Dict, Any

from ..database import get_db, DATA_DIR
from ..models import User, Board, Person, Group, Account, AuthToken, AuditLog, SystemConfig
from ..auth import require_admin, hash_password, create_token, revoke_user_tokens, validate_password_strength

router = APIRouter(prefix="/api/admin", tags=["admin"])

class UserListItem(BaseModel):
    uid: str
    username: str
    role: str
    enabled: bool
    avatar: Optional[str] = None
    board_count: int = 0
    created_at: Optional[str] = None
    last_login: Optional[str] = None
    limits: Dict[str, Any] = {}
    model_config = {"from_attributes": True}

class UserCreatePayload(BaseModel):
    username: str = Field(..., min_length=2, max_length=50)
    password: str = Field(..., min_length=8, max_length=128)
    role: str = Field(default="user", pattern="^(user|admin)$")
    enabled: bool = True
    limits: Dict[str, Any] = {}

class UserUpdatePayload(BaseModel):
    username: Optional[str] = Field(default=None, min_length=2, max_length=50)
    role: Optional[str] = Field(default=None, pattern="^(user|admin)$")
    enabled: Optional[bool] = None
    limits: Optional[Dict[str, Any]] = None

class ConfigPayload(BaseModel):
    key: str
    value: str

def _generate_password(length: int = 12) -> str:
    alphabet = string.ascii_letters + string.digits
    return ''.join(secrets.choice(alphabet) for _ in range(length))

@router.get("/users", response_model=list[UserListItem])
def list_users(
    search: str = Query(default=""),
    role: str = Query(default=""),
    enabled: Optional[bool] = Query(default=None),
    db: Session = Depends(get_db),
    admin: dict = Depends(require_admin),
):
    from datetime import datetime, timezone
    query = db.query(User)
    if search:
        query = query.filter(User.username.ilike(f"%{search}%"))
    if role:
        query = query.filter(User.role == role)
    if enabled is not None:
        query = query.filter(User.enabled == enabled)

    users = query.order_by(User.created_at.desc()).all()
    result = []
    for u in users:
        board_count = db.query(Board).filter(Board.user_id == u.id).count()
        last_token = (
            db.query(AuthToken).filter(AuthToken.username == u.username)
            .order_by(AuthToken.created_at.desc()).first()
        )
        last_login = last_token.created_at.isoformat() if last_token else None
        result.append(UserListItem(
            uid=u.uid,
            username=u.username,
            role=u.role,
            enabled=u.enabled,
            avatar=u.avatar,
            board_count=board_count,
            created_at=u.created_at.isoformat() if u.created_at else None,
            last_login=last_login,
            limits=json.loads(u.limits or "{}"),
        ))
    return result

@router.post("/users", response_model=UserListItem, status_code=201)
def create_user(data: UserCreatePayload, db: Session = Depends(get_db), admin: dict = Depends(require_admin)):
    existing = db.query(User).filter(User.username == data.username).first()
    if existing:
        raise HTTPException(status_code=409, detail="用户名已存在")
    err = validate_password_strength(data.password)
    if err:
        raise HTTPException(status_code=400, detail=err)
    u = User(
        uid="0",
        username=data.username,
        password_hash=hash_password(data.password),
        role=data.role,
        enabled=data.enabled,
        limits=json.dumps(data.limits, ensure_ascii=False),
    )
    db.add(u)
    db.flush()
    u.uid = str(u.id)
    from ..audit import log as audit_log
    audit_log(db, admin["username"], "create", "user", u.id, {"username": data.username, "role": data.role})
    db.commit()
    db.refresh(u)
    return UserListItem(
        uid=u.uid, username=u.username, role=u.role, enabled=u.enabled,
        avatar=u.avatar, board_count=0,
        created_at=u.created_at.isoformat() if u.created_at else None,
        limits=json.loads(u.limits or "{}"),
    )

@router.put("/users/{uid}", response_model=UserListItem)
def update_user(uid: str, data: UserUpdatePayload, db: Session = Depends(get_db), admin: dict = Depends(require_admin)):
    u = db.query(User).filter(User.uid == uid).first()
    if not u:
        raise HTTPException(status_code=404, detail="用户不存在")

    if data.username is not None and data.username != u.username:
        existing = db.query(User).filter(User.username == data.username).first()
        if existing:
            raise HTTPException(status_code=409, detail="用户名已占用")
        old_username = u.username
        u.username = data.username
        revoke_user_tokens(old_username)

    if data.role is not None:
        if u.uid == admin["uid"] and data.role != "admin":
            raise HTTPException(status_code=400, detail="不能降级自己的管理员角色")
        u.role = data.role

    if data.enabled is not None:
        if u.uid == admin["uid"] and not data.enabled:
            raise HTTPException(status_code=400, detail="不能禁用自己")
        u.enabled = data.enabled

    if data.limits is not None:
        u.limits = json.dumps(data.limits, ensure_ascii=False)

    from ..audit import log as audit_log
    audit_log(db, admin["username"], "update", "user", u.id, data.model_dump(exclude_unset=True))
    db.commit()
    db.refresh(u)
    board_count = db.query(Board).filter(Board.user_id == u.id).count()
    return UserListItem(
        uid=u.uid, username=u.username, role=u.role, enabled=u.enabled,
        avatar=u.avatar, board_count=board_count,
        created_at=u.created_at.isoformat() if u.created_at else None,
        limits=json.loads(u.limits or "{}"),
    )

@router.delete("/users/{uid}", status_code=204)
def delete_user(uid: str, db: Session = Depends(get_db), admin: dict = Depends(require_admin)):
    if uid == admin["uid"]:
        raise HTTPException(status_code=400, detail="不能删除自己")
    u = db.query(User).filter(User.uid == uid).first()
    if not u:
        raise HTTPException(status_code=404, detail="用户不存在")

    from ..audit import log as audit_log
    audit_log(db, admin["username"], "delete", "user", u.id, {"username": u.username})

    boards = db.query(Board).filter(Board.user_id == u.id).all()
    for board in boards:
        db.delete(board)

    revoke_user_tokens(u.username)
    db.delete(u)
    db.commit()

    user_upload_dir = os.path.join(DATA_DIR, "uploads", uid)
    if os.path.exists(user_upload_dir):
        shutil.rmtree(user_upload_dir, ignore_errors=True)

@router.post("/users/{uid}/reset-password")
def reset_user_password(uid: str, db: Session = Depends(get_db), admin: dict = Depends(require_admin)):
    u = db.query(User).filter(User.uid == uid).first()
    if not u:
        raise HTTPException(status_code=404, detail="用户不存在")
    new_password = _generate_password(12)
    u.password_hash = hash_password(new_password)
    revoke_user_tokens(u.username)
    from ..audit import log as audit_log
    audit_log(db, admin["username"], "update", "user", u.id, {"action": "reset_password"})
    db.commit()
    return {"uid": uid, "new_password": new_password}

@router.post("/users/{uid}/force-logout")
def force_logout(uid: str, db: Session = Depends(get_db), admin: dict = Depends(require_admin)):
    u = db.query(User).filter(User.uid == uid).first()
    if not u:
        raise HTTPException(status_code=404, detail="用户不存在")
    revoke_user_tokens(u.username)
    from ..audit import log as audit_log
    audit_log(db, admin["username"], "update", "user", u.id, {"action": "force_logout"})
    db.commit()
    return {"status": "ok", "message": f"已强制下线用户 {u.username}"}

@router.get("/dashboard")
def dashboard(db: Session = Depends(get_db), admin: dict = Depends(require_admin)):
    from datetime import datetime, timezone, timedelta
    total_users = db.query(User).count()
    total_boards = db.query(Board).count()
    total_persons = db.query(Person).count()
    total_accounts = db.query(Account).count()

    week_ago = datetime.now(timezone.utc) - timedelta(days=7)
    new_users_7d = db.query(User).filter(User.created_at >= week_ago).count()
    new_persons_7d = db.query(Person).filter(Person.created_at >= week_ago).count()

    user_storage = []
    uploads_root = os.path.join(DATA_DIR, "uploads")
    if os.path.exists(uploads_root):
        for uid in os.listdir(uploads_root):
            user_dir = os.path.join(uploads_root, uid)
            if os.path.isdir(user_dir):
                size = sum(
                    os.path.getsize(os.path.join(dp, f))
                    for dp, _, filenames in os.walk(user_dir)
                    for f in filenames
                )
                user_storage.append({"uid": uid, "size_bytes": size})

    total_storage = sum(item["size_bytes"] for item in user_storage)

    return {
        "total_users": total_users,
        "total_boards": total_boards,
        "total_persons": total_persons,
        "total_accounts": total_accounts,
        "new_users_7d": new_users_7d,
        "new_persons_7d": new_persons_7d,
        "total_storage_bytes": total_storage,
        "user_storage": user_storage[:50],
    }

@router.get("/audit-logs")
def list_audit_logs(
    username: str = Query(default=""),
    action: str = Query(default=""),
    target_type: str = Query(default=""),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=50, ge=1, le=200),
    db: Session = Depends(get_db),
    admin: dict = Depends(require_admin),
):
    query = db.query(AuditLog)
    if username:
        query = query.filter(AuditLog.username.ilike(f"%{username}%"))
    if action:
        query = query.filter(AuditLog.action == action)
    if target_type:
        query = query.filter(AuditLog.target_type == target_type)

    total = query.count()
    logs = query.order_by(AuditLog.created_at.desc()).offset((page - 1) * page_size).limit(page_size).all()

    return {
        "total": total,
        "page": page,
        "page_size": page_size,
        "items": [
            {
                "id": log.id,
                "username": log.username,
                "action": log.action,
                "target_type": log.target_type,
                "target_id": log.target_id,
                "details": json.loads(log.details) if log.details else None,
                "created_at": log.created_at.isoformat() if log.created_at else None,
            }
            for log in logs
        ],
    }

@router.get("/config")
def get_config(db: Session = Depends(get_db), admin: dict = Depends(require_admin)):
    configs = db.query(SystemConfig).all()
    return {c.key: c.value for c in configs}

@router.put("/config")
def update_config(data: ConfigPayload, db: Session = Depends(get_db), admin: dict = Depends(require_admin)):
    cfg = db.query(SystemConfig).filter(SystemConfig.key == data.key).first()
    if not cfg:
        cfg = SystemConfig(key=data.key, value=data.value)
        db.add(cfg)
    else:
        cfg.value = data.value
    from ..audit import log as audit_log
    audit_log(db, admin["username"], "update", "config", None, {"key": data.key, "value": data.value})
    db.commit()
    return {"key": data.key, "value": data.value}

public_router = APIRouter(prefix="/api/public", tags=["public"])


@public_router.get("/config")
def get_public_config(db: Session = Depends(get_db)):
    configs = db.query(SystemConfig).all()
    return {c.key: c.value for c in configs}
