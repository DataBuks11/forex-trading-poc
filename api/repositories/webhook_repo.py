from database import get_db
from datetime import datetime


def log_webhook(user_id: int, symbol: str, action: str, lot: float,
                sl: float, tp: float, status: str = "pending",
                message: str = "", ticket: int | None = None) -> int:
    db = get_db()
    try:
        db.execute("""INSERT INTO webhook_logs (user_id, symbol, action, lot, sl, tp, status, message, ticket, received_at)
            VALUES (?,?,?,?,?,?,?,?,?,?)""",
                   (user_id, symbol, action, lot, sl, tp, status, message, ticket,
                    datetime.utcnow().isoformat()))
        db.commit()
        return db.execute("SELECT last_insert_rowid()").fetchone()[0]
    finally:
        db.close()


def update_webhook_status(log_id: int, status: str, message: str = "", ticket: int | None = None):
    db = get_db()
    try:
        db.execute("UPDATE webhook_logs SET status=?, message=?, ticket=?, executed_at=? WHERE id=?",
                   (status, message, ticket, datetime.utcnow().isoformat(), log_id))
        db.commit()
    finally:
        db.close()


def get_webhook_logs(user_id: int, limit: int = 50) -> list:
    db = get_db()
    try:
        rows = db.execute(
            "SELECT * FROM webhook_logs WHERE user_id=? ORDER BY received_at DESC LIMIT ?",
            (user_id, limit)).fetchall()
        return [dict(r) for r in rows]
    finally:
        db.close()


def get_last_webhook(user_id: int) -> dict | None:
    db = get_db()
    try:
        row = db.execute(
            "SELECT * FROM webhook_logs WHERE user_id=? ORDER BY received_at DESC LIMIT 1",
            (user_id,)).fetchone()
        return dict(row) if row else None
    finally:
        db.close()
