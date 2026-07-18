from database import get_db
from datetime import datetime
import secrets


def get_settings(user_id: int) -> dict:
    db = get_db()
    try:
        row = db.execute("SELECT * FROM settings WHERE user_id=?", (user_id,)).fetchone()
        if not row:
            secret = secrets.token_hex(16)
            db.execute(
                "INSERT INTO settings (user_id, webhook_secret) VALUES (?,?)",
                (user_id, secret))
            db.commit()
            row = db.execute("SELECT * FROM settings WHERE user_id=?", (user_id,)).fetchone()
        return dict(row) if row else {}
    finally:
        db.close()


def update_settings(user_id: int, data: dict) -> bool:
    db = get_db()
    try:
        existing = db.execute("SELECT id FROM settings WHERE user_id=?", (user_id,)).fetchone()
        now = datetime.utcnow().isoformat()
        if existing:
            sets = ", ".join(f"{k}=?" for k in data)
            db.execute(f"UPDATE settings SET {sets}, updated_at=? WHERE user_id=?",
                       (*data.values(), now, user_id))
        else:
            data["user_id"] = user_id
            keys = ", ".join(data.keys())
            placeholders = ", ".join("?" for _ in data)
            db.execute(f"INSERT INTO settings ({keys}) VALUES ({placeholders})", tuple(data.values()))
        db.commit()
        return True
    finally:
        db.close()


def get_webhook_secret(user_id: int) -> str:
    settings = get_settings(user_id)
    return settings.get("webhook_secret", "")


def regenerate_secret(user_id: int) -> str:
    secret = secrets.token_hex(16)
    update_settings(user_id, {"webhook_secret": secret})
    return secret
