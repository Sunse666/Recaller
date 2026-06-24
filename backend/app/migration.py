import secrets
import string
from sqlalchemy import text, inspect
from sqlalchemy.orm import Session

_UID_ALPHABET = string.ascii_letters + string.digits + "-_"

def _nanoid(size=21) -> str:
    return "".join(secrets.choice(_UID_ALPHABET) for _ in range(size))

def run_migration(db: Session):
    _migrate_admin_users(db)
    _add_board_id_columns(db)
    _add_board_label_columns(db)
    _ensure_default_board(db)
    db.commit()

def _has_table(db: Session, name: str) -> bool:
    try:
        db.execute(text(f"SELECT 1 FROM {name} LIMIT 1"))
        return True
    except Exception:
        return False

def _column_exists(db: Session, table: str, column: str) -> bool:
    try:
        rows = db.execute(text(f"PRAGMA table_info('{table}')")).fetchall()
        return any(r[1] == column for r in rows)
    except Exception:
        return False

def _migrate_admin_users(db: Session):
    if not _has_table(db, "admin_users"):
        return
    users_exist = db.execute(text("SELECT COUNT(*) FROM users")).scalar()
    if users_exist and users_exist > 0:
        return
    admins = db.execute(text("SELECT id, username, password_hash, created_at FROM admin_users")).fetchall()
    for row in admins:
        existing = db.execute(
            text("SELECT id FROM users WHERE username = :u"), {"u": row[1]}
        ).fetchone()
        if existing:
            continue
        db.execute(
            text("INSERT INTO users (uid, username, password_hash, role, created_at) VALUES ('0', :u, :ph, 'admin', :ca)"),
            {"u": row[1], "ph": row[2], "ca": row[3] or _utcnow_str()},
        )
        db.commit()
        new_id = db.execute(text("SELECT id FROM users WHERE username = :u"), {"u": row[1]}).scalar()
        if new_id:
            db.execute(text("UPDATE users SET uid = :uid WHERE id = :id"), {"uid": str(new_id), "id": new_id})
    db.execute(text("DROP TABLE IF EXISTS admin_users"))
    db.commit()
    users = db.execute(text("SELECT id, uid FROM users")).fetchall()
    for u in users:
        if u[1] != str(u[0]):
            db.execute(text("UPDATE users SET uid = :uid WHERE id = :id"), {"uid": str(u[0]), "id": u[0]})
    db.commit()

def _add_board_id_columns(db: Session):
    for table in ("persons", "groups", "accounts"):
        if not _column_exists(db, table, "board_id"):
            db.execute(text(f"ALTER TABLE {table} ADD COLUMN board_id INTEGER REFERENCES boards(id) ON DELETE CASCADE"))
    db.commit()

def _add_board_label_columns(db: Session):
    for col, default in [("group_label", "群"), ("groups_label", "群组")]:
        if not _column_exists(db, "boards", col):
            db.execute(text(f"ALTER TABLE boards ADD COLUMN {col} VARCHAR(50) NOT NULL DEFAULT '{default}'"))
    db.commit()

def _ensure_default_board(db: Session):
    board_count = db.execute(text("SELECT COUNT(*) FROM boards")).scalar()
    if board_count and board_count > 0:
        return
    admin = db.execute(
        text("SELECT id FROM users WHERE role = 'admin' ORDER BY id LIMIT 1")
    ).fetchone()
    if not admin:
        return
    db.execute(
        text(
            "INSERT INTO boards (user_id, name, icon, description, card_label, cards_label, group_label, groups_label, field_config, is_public, sort_order) "
            "VALUES (:uid, '默认看板', '👥', '默认看板', '群友', '群友们', '群', '群组', '{}', 1, 0)"
        ),
        {"uid": admin[0]},
    )
    db.commit()
    default_id = db.execute(text("SELECT id FROM boards ORDER BY id LIMIT 1")).scalar()
    for table in ("persons", "groups", "accounts"):
        db.execute(text(f"UPDATE {table} SET board_id = :bid WHERE board_id IS NULL"), {"bid": default_id})
    db.commit()

def _utcnow_str() -> str:
    import datetime
    return datetime.datetime.now(datetime.timezone.utc).isoformat()
