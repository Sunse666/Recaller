import os
from cryptography.fernet import Fernet

_KEY_FILE = os.path.join(os.path.dirname(os.path.dirname(__file__)), "encryption.key")
_KEY: bytes | None = None

def _get_key() -> bytes:
    global _KEY
    if _KEY:
        return _KEY

    env_key = os.environ.get("ENCRYPTION_KEY")
    if env_key:
        _KEY = env_key.encode() if len(env_key) < 50 else env_key.encode()
        return _KEY

    if os.path.exists(_KEY_FILE):
        with open(_KEY_FILE, "rb") as f:
            _KEY = f.read()
        return _KEY

    _KEY = Fernet.generate_key()
    with open(_KEY_FILE, "wb") as f:
        f.write(_KEY)
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
