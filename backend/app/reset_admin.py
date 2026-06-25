import os
import sys
import secrets
import string
import sqlite3

DB_PATH = os.environ.get("DATA_DIR", os.path.join(os.path.dirname(os.path.dirname(__file__)), "data"))
DB_PATH = os.path.join(DB_PATH, "recaller.db")


def get_conn():
    return sqlite3.connect(DB_PATH)


def hash_password(password: str) -> str:
    import bcrypt
    return bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()


def reset_admin():
    if not os.path.exists(DB_PATH):
        print(f"[错误] 数据库文件不存在: {DB_PATH}")
        sys.exit(1)

    alphabet = string.ascii_letters + string.digits
    new_password = ''.join(secrets.choice(alphabet) for _ in range(16))

    conn = get_conn()
    try:
        user = conn.execute(
            "SELECT id, username, role FROM users WHERE uid = '1'"
        ).fetchone()

        if not user:
            print("[错误] 找不到 uid=1 的 admin 用户")
            sys.exit(1)

        hashed = hash_password(new_password)

        conn.execute(
            "UPDATE users SET password_hash = ?, role = 'superadmin' WHERE uid = '1'",
            (hashed,),
        )
        conn.execute("DELETE FROM auth_tokens WHERE uid = '1'")
        conn.commit()

        print(f"admin 已重置")
        print(f"  用户名: {user[1]}")
        print(f"  角色: superadmin")
        print(f"  新密码: {new_password}")
        print(f"  已强制下线所有会话")

    except Exception as e:
        print(f"[错误] {e}")
        sys.exit(1)
    finally:
        conn.close()


if __name__ == "__main__":
    reset_admin()
