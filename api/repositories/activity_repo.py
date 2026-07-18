from database import get_db
from datetime import datetime
import json


def log_activity(user_id: int, event_type: str, description: str, metadata: dict | None = None):
    db = get_db()
    try:
        db.execute(
            "INSERT INTO activity_logs (user_id, event_type, description, metadata) VALUES (?,?,?,?)",
            (user_id, event_type, description, json.dumps(metadata or {})),
        )
        db.commit()
    finally:
        db.close()


def get_activity_logs(user_id: int, limit: int = 50) -> list:
    db = get_db()
    try:
        rows = db.execute(
            "SELECT * FROM activity_logs WHERE user_id=? ORDER BY created_at DESC LIMIT ?",
            (user_id, limit)).fetchall()
        return [dict(r) for r in rows]
    finally:
        db.close()
