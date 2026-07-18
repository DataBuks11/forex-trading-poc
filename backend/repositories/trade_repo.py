from database import get_db
from datetime import datetime


def save_trade(user_id: int, symbol: str, action: str, lot: float, sl: float, tp: float,
               ticket: int | None, open_price: float, source: str = "webhook",
               broker: str = "") -> int:
    db = get_db()
    try:
        db.execute("""INSERT INTO trades (user_id, symbol, action, lot, sl, tp, ticket,
            open_price, status, source, broker) VALUES (?,?,?,?,?,?,?,?,'OPEN',?,?)""",
                   (user_id, symbol, action, lot, sl, tp, ticket, open_price, source, broker))
        db.commit()
        return db.execute("SELECT last_insert_rowid()").fetchone()[0]
    finally:
        db.close()


def get_trade_history(user_id: int, limit: int = 50, offset: int = 0,
                      symbol: str = "", action: str = "", status: str = "") -> list:
    db = get_db()
    try:
        query = "SELECT * FROM trades WHERE user_id=?"
        params = [user_id]
        if symbol:
            query += " AND symbol LIKE ?"
            params.append(f"%{symbol}%")
        if action:
            query += " AND action=?"
            params.append(action)
        if status:
            query += " AND status=?"
            params.append(status)
        query += " ORDER BY created_at DESC LIMIT ? OFFSET ?"
        params.extend([limit, offset])
        rows = db.execute(query, params).fetchall()
        return [dict(r) for r in rows]
    finally:
        db.close()


def get_open_trades(user_id: int) -> list:
    db = get_db()
    try:
        rows = db.execute(
            "SELECT * FROM trades WHERE user_id=? AND status='OPEN' ORDER BY created_at DESC",
            (user_id,)).fetchall()
        return [dict(r) for r in rows]
    finally:
        db.close()


def close_trade(trade_id: int, close_price: float, profit: float) -> bool:
    db = get_db()
    try:
        db.execute("""UPDATE trades SET status='CLOSED', close_price=?, profit=?,
            closed_at=? WHERE id=?""", (close_price, profit, datetime.utcnow().isoformat(), trade_id))
        db.commit()
        return True
    finally:
        db.close()


def get_trade_count(user_id: int) -> int:
    db = get_db()
    try:
        return db.execute("SELECT COUNT(*) FROM trades WHERE user_id=?", (user_id,)).fetchone()[0]
    finally:
        db.close()
