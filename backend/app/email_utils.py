import os
import random
import smtplib
import time
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime, timezone, timedelta
from sqlalchemy.orm import Session

from .models import EmailVerification

SMTP_HOST = os.environ.get("SMTP_HOST", "smtp.resend.com")
SMTP_PORT = int(os.environ.get("SMTP_PORT", "587"))
SMTP_USER = os.environ.get("SMTP_USER", "resend")
SMTP_PASS = os.environ.get("SMTP_PASS", "")
SMTP_FROM = os.environ.get("SMTP_FROM", "no-reply@recaller.local")
SMTP_USE_TLS = os.environ.get("SMTP_USE_TLS", "true").lower() == "true"

CODE_LENGTH = 6
CODE_EXPIRE_MINUTES = 60
MAX_ATTEMPTS = 5

_send_log: dict[str, list[float]] = {}

def _check_rate(key: str, max_per_min: int = 1) -> bool:
    """同一 key（邮箱或 IP）每分钟最多 max_per_min 次"""
    now = time.time()
    entries = [t for t in _send_log.get(key, []) if now - t < 60]
    _send_log[key] = entries
    if len(entries) >= max_per_min:
        return False
    entries.append(now)
    return True

def generate_code() -> str:
    return ''.join(str(random.randint(0, 9)) for _ in range(CODE_LENGTH))

def send_email(to: str, subject: str, html_body: str) -> bool:
    msg = MIMEMultipart("alternative")
    msg["From"] = SMTP_FROM
    msg["To"] = to
    msg["Subject"] = subject
    msg.attach(MIMEText(html_body, "html", "utf-8"))

    try:
        if SMTP_USE_TLS:
            server = smtplib.SMTP(SMTP_HOST, SMTP_PORT, timeout=10)
            server.starttls()
        else:
            server = smtplib.SMTP_SSL(SMTP_HOST, SMTP_PORT, timeout=10)
        server.login(SMTP_USER, SMTP_PASS)
        server.sendmail(SMTP_FROM, [to], msg.as_string())
        server.quit()
        return True
    except Exception as e:
        print(f"[email] 发送失败: {e}")
        return False

def send_verification_code(db: Session, email: str, purpose: str, ip: str) -> str | None:
    if not SMTP_PASS:
        return "邮件服务未配置"

    if not _check_rate(email):
        return "发送过于频繁，请 60 秒后再试"
    if not _check_rate(f"ip:{ip}", max_per_min=3):
        return "发送过于频繁，请稍后再试"

    code = generate_code()
    now = datetime.now(timezone.utc)
    expires = now + timedelta(minutes=CODE_EXPIRE_MINUTES)

    db.query(EmailVerification).filter(
        EmailVerification.email == email,
        EmailVerification.purpose == purpose,
        EmailVerification.used == False,
    ).update({"used": True})
    db.commit()

    entry = EmailVerification(
        email=email,
        code=code,
        purpose=purpose,
        expires_at=expires,
    )
    db.add(entry)
    db.commit()

    purpose_text = "注册" if purpose == "register" else "登录"
    html = f"""
    <div style="font-family:sans-serif;max-width:480px;margin:0 auto;padding:24px">
      <h2 style="color:#f472b6">Recaller · 图片记忆助手</h2>
      <p>你的{purpose_text}验证码（{CODE_EXPIRE_MINUTES}分钟内有效）：</p>
      <p style="font-size:32px;letter-spacing:8px;font-weight:bold;color:#f472b6;margin:16px 0">{code}</p>
      <p style="color:#999;font-size:13px">如果这不是你本人操作，请忽略此邮件。</p>
    </div>
    """

    if not send_email(email, f"Recaller {purpose_text}验证码: {code}", html):
        return "邮件发送失败，请稍后再试"

    return None

def verify_code(db: Session, email: str, code: str, purpose: str) -> str | None:
    """校验验证码，返回 None 表示成功，否则返回错误文字。"""
    now = datetime.now(timezone.utc)
    entry = (
        db.query(EmailVerification)
        .filter(
            EmailVerification.email == email,
            EmailVerification.purpose == purpose,
            EmailVerification.used == False,
            EmailVerification.expires_at > now,
        )
        .order_by(EmailVerification.created_at.desc())
        .first()
    )

    if not entry:
        return "验证码已过期或不存在，请重新发送"

    entry.attempts += 1
    db.commit()

    if entry.attempts > MAX_ATTEMPTS:
        entry.used = True
        db.commit()
        return "验证码尝试次数过多，已失效"

    if entry.code != code:
        return "验证码错误"

    entry.used = True
    db.commit()
    return None
