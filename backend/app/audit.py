import json
from datetime import datetime, timezone
from sqlalchemy.orm import Session
from .models import AuditLog

def log(db: Session, username: str, action: str, target_type: str, target_id: int | None = None, details: dict | None = None):
    entry = AuditLog(
        username=username,
        action=action,
        target_type=target_type,
        target_id=target_id,
        details=json.dumps(details, ensure_ascii=False) if details else None,
    )
    db.add(entry)
