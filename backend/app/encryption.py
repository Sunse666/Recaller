import os
import hashlib
import base64
from cryptography.fernet import Fernet

_KEY_FILE = os.path.join(os.path.dirname(os.path.dirname(__file__)), "encryption.key")
_KEY: bytes | None = None

def _derive_key(raw: bytes) -> bytes:
    """Derive a valid Fernet key from arbitrary input using SHA-256 + base64."""
    digest = hashlib.sha256(raw).digest()
    return base64.urlsafe_b64encode(digest)

def _get_key() -> bytes:
    global _KEY
    if _KEY:
        return _KEY

    env_key = os.environ.get("ENCRYPTION_KEY")
    if env_key:
        raw = env_key.encode()
        _KEY = _derive_key(raw) if len(raw) < 32 else (
            raw if len(raw) == 44 and raw[-1:] == b"=" else _derive_key(raw)
        )
        return _KEY

    if os.path.exists(_KEY_FILE):
        with open(_KEY_FILE, "rb") as f:
            raw = f.read().strip()
        if len(raw) == 44 and raw[-1:] == 61:
            _KEY = raw
        else:
            _KEY = _derive_key(raw)
        return _KEY

    _KEY = Fernet.generate_key()
    with open(_KEY_FILE, "wb") as f:
        f.write(_KEY)
    print("[encryption] 已生成新的加密密钥，请备份 encryption.key 文件！丢失此文件将导致所有加密数据无法恢复。")
    return _KEY

def encrypt(text: str | None) -> str | None:
    if not text:
        return text
    f = Fernet(_get_key())
    return f.encrypt(text.encode()).decode()

def decrypt(text: str | None) -> str | None:
    if not text:
        return text
    try:
        f = Fernet(_get_key())
        return f.decrypt(text.encode()).decode()
    except Exception:
        return text
