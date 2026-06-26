from sqlalchemy import text, inspect
from sqlalchemy.orm import Session

def run_migration(db: Session):
    _migrate_admin_users(db)
    _add_board_id_columns(db)
    _add_board_label_columns(db)
    _add_person_card_bg(db)
    _add_user_avatar(db)
    _add_board_type(db)
    _add_user_enabled(db)
    _create_system_config(db)
    _add_user_limits(db)
    _bump_user_auto_uid(db)
    _upgrade_admin_to_superadmin(db)
    _add_user_email(db)
    _create_email_verifications(db)
    _add_person_allow_download(db)
    _add_board_random_order(db)
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
    for col, default in [("group_label", "图组"), ("groups_label", "图组")]:
        if not _column_exists(db, "boards", col):
            db.execute(text(f"ALTER TABLE boards ADD COLUMN {col} VARCHAR(50) NOT NULL DEFAULT '{default}'"))
    db.commit()

def _add_person_card_bg(db: Session):
    if not _column_exists(db, "persons", "card_bg"):
        db.execute(text("ALTER TABLE persons ADD COLUMN card_bg VARCHAR(2000)"))
    db.commit()

def _add_user_avatar(db: Session):
    if not _column_exists(db, "users", "avatar"):
        db.execute(text("ALTER TABLE users ADD COLUMN avatar VARCHAR(500)"))
    db.commit()

def _add_board_type(db: Session):
    if not _column_exists(db, "boards", "board_type"):
        db.execute(text("ALTER TABLE boards ADD COLUMN board_type VARCHAR(20) NOT NULL DEFAULT 'image'"))
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
            "INSERT INTO boards (user_id, name, icon, description, card_label, cards_label, group_label, groups_label, board_type, field_config, is_public, sort_order) "
            "VALUES (:uid, '默认画板', '', '默认画板', '图片', '图片', '图组', '图组', 'image', '{}', 1, 0)"
        ),
        {"uid": admin[0]},
    )
    db.commit()
    default_id = db.execute(text("SELECT id FROM boards ORDER BY id LIMIT 1")).scalar()
    for table in ("persons", "groups", "accounts"):
        db.execute(text(f"UPDATE {table} SET board_id = :bid WHERE board_id IS NULL"), {"bid": default_id})
    db.commit()

def _add_user_enabled(db: Session):
    if not _column_exists(db, "users", "enabled"):
        db.execute(text("ALTER TABLE users ADD COLUMN enabled BOOLEAN NOT NULL DEFAULT 1"))
    db.commit()

def _create_system_config(db: Session):
    if not _has_table(db, "system_config"):
        db.execute(text("CREATE TABLE system_config (key VARCHAR(50) PRIMARY KEY, value TEXT NOT NULL)"))
        db.execute(text("INSERT INTO system_config (key, value) VALUES ('registration_open', '1')"))
        db.execute(text("INSERT INTO system_config (key, value) VALUES ('site_name', '图片展示')"))
    db.commit()

def _add_user_limits(db: Session):
    if not _column_exists(db, "users", "limits"):
        db.execute(text("ALTER TABLE users ADD COLUMN limits TEXT NOT NULL DEFAULT '{}'"))
    db.commit()

def _upgrade_admin_to_superadmin(db: Session):
    """将现有 role='admin' 的用户升级为 'superadmin'"""
    db.execute(text("UPDATE users SET role = 'superadmin' WHERE role = 'admin'"))
    db.commit()

def _bump_user_auto_uid(db: Session):
    """将 users 表自增起点推到 11，使新用户自动 UID 从 11 开始。仅当最大 id < 10 时执行。"""
    try:
        max_id = db.execute(text("SELECT COALESCE(MAX(id), 0) FROM users")).scalar()
        if max_id < 10:
            db.execute(text("UPDATE sqlite_sequence SET seq = 10 WHERE name = 'users'"))
    except Exception:
        pass
    db.commit()

def _add_user_email(db: Session):
    for col in [("email", "VARCHAR(200)"), ("email_verified", "BOOLEAN NOT NULL DEFAULT 0")]:
        if not _column_exists(db, "users", col[0]):
            db.execute(text(f"ALTER TABLE users ADD COLUMN {col[0]} {col[1]}"))
    db.commit()

def _create_email_verifications(db: Session):
    if not _has_table(db, "email_verifications"):
        db.execute(text("""
            CREATE TABLE email_verifications (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                email VARCHAR(200) NOT NULL,
                code VARCHAR(10) NOT NULL,
                purpose VARCHAR(20) NOT NULL DEFAULT 'register',
                expires_at DATETIME NOT NULL,
                used BOOLEAN NOT NULL DEFAULT 0,
                attempts INTEGER NOT NULL DEFAULT 0,
                created_at DATETIME
            )
        """))
    db.commit()

def _add_person_allow_download(db: Session):
    if not _column_exists(db, "persons", "allow_download"):
        db.execute(text("ALTER TABLE persons ADD COLUMN allow_download BOOLEAN NOT NULL DEFAULT 0"))
    db.commit()

def _add_board_random_order(db: Session):
    if not _column_exists(db, "boards", "random_order"):
        db.execute(text("ALTER TABLE boards ADD COLUMN random_order BOOLEAN NOT NULL DEFAULT 0"))
    db.commit()

def _utcnow_str() -> str:
    import datetime
    return datetime.datetime.now(datetime.timezone.utc).isoformat()
