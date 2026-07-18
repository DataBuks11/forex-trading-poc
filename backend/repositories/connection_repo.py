from database import get_db
from datetime import datetime


def save_connection(user_id: int, broker_name: str, login_id: int, password: str,
                    server_name: str, account_info: dict) -> bool:
    db = get_db()
    try:
        now = datetime.utcnow().isoformat()
        existing = db.execute("SELECT id FROM mt5_connections WHERE user_id=?", (user_id,)).fetchone()
        if existing:
            db.execute("""UPDATE mt5_connections SET broker_name=?, login_id=?, password=?, server_name=?,
                is_connected=1, account_number=?, balance=?, equity=?, margin=?, free_margin=?,
                leverage=?, currency=?, terminal_version=?, connection_time=?, is_demo=?, updated_at=?
                WHERE user_id=?""", (
                broker_name, login_id, password, server_name,
                account_info.get("account_number", 0), account_info.get("balance", 0),
                account_info.get("equity", 0), account_info.get("margin", 0),
                account_info.get("free_margin", 0), account_info.get("leverage", 0),
                account_info.get("currency", "USD"), account_info.get("terminal_version", ""),
                now, 1 if "demo" in broker_name.lower() else 0, now, user_id))
        else:
            db.execute("""INSERT INTO mt5_connections (user_id, broker_name, login_id, password, server_name,
                is_connected, account_number, balance, equity, margin, free_margin, leverage, currency,
                terminal_version, connection_time, is_demo, updated_at)
                VALUES (?,?,?,?,?,1,?,?,?,?,?,?,?,?,?,?,?)""", (
                user_id, broker_name, login_id, password, server_name,
                account_info.get("account_number", 0), account_info.get("balance", 0),
                account_info.get("equity", 0), account_info.get("margin", 0),
                account_info.get("free_margin", 0), account_info.get("leverage", 0),
                account_info.get("currency", "USD"), account_info.get("terminal_version", ""),
                now, 1 if "demo" in broker_name.lower() else 0, now))
        db.commit()
        return True
    finally:
        db.close()


def get_connection(user_id: int) -> dict | None:
    db = get_db()
    try:
        row = db.execute("SELECT * FROM mt5_connections WHERE user_id=? AND is_connected=1", (user_id,)).fetchone()
        return dict(row) if row else None
    finally:
        db.close()


def disconnect(user_id: int):
    db = get_db()
    try:
        db.execute("UPDATE mt5_connections SET is_connected=0 WHERE user_id=?", (user_id,))
        db.commit()
    finally:
        db.close()


def update_account_info(user_id: int, info: dict):
    db = get_db()
    try:
        db.execute("""UPDATE mt5_connections SET balance=?, equity=?, margin=?, free_margin=?,
            updated_at=? WHERE user_id=?""", (
            info.get("balance", 0), info.get("equity", 0), info.get("margin", 0),
            info.get("free_margin", 0), datetime.utcnow().isoformat(), user_id))
        db.commit()
    finally:
        db.close()
