import json
from fastapi import APIRouter, HTTPException, Depends, Query
from middleware import get_current_user, TokenData
from database import get_db
from datetime import datetime

router = APIRouter(prefix="/api/scripts", tags=["Trading Scripts"])


def is_admin(user_id: int) -> bool:
    return user_id == 1


@router.get("")
def list_scripts(user: TokenData = Depends(get_current_user)):
    """Get all available trading scripts."""
    db = get_db()
    try:
        rows = db.execute("SELECT * FROM trading_scripts WHERE is_active=1 OR created_by=? ORDER BY created_at DESC", 
                         (user.user_id,)).fetchall()
        scripts = []
        for r in rows:
            s = dict(r)
            s["script_config"] = json.loads(s["script_config"]) if s["script_config"] else {}
            us = db.execute("SELECT * FROM user_scripts WHERE user_id=? AND script_id=?", 
                           (user.user_id, s["id"])).fetchone()
            s["user_enabled"] = bool(us["is_enabled"]) if us else False
            s["user_lot"] = us["custom_lot_size"] if us else s.get("custom_lot_size", 0.01)
            scripts.append(s)
        return scripts
    finally:
        db.close()


@router.post("")
def create_script(data: dict, user: TokenData = Depends(get_current_user)):
    """Create a new trading script."""
    db = get_db()
    try:
        is_admin_only = data.get("is_admin_only", False) and is_admin(user.user_id)
        db.execute(
            "INSERT INTO trading_scripts (name, description, symbol, timeframe, script_config, created_by, is_admin_only) VALUES (?,?,?,?,?,?,?)",
            (data["name"], data.get("description", ""), data.get("symbol", "EURUSD"),
             data.get("timeframe", "M5"), json.dumps(data.get("script_config", {})), user.user_id, is_admin_only)
        )
        db.commit()
        sid = db.execute("SELECT last_insert_rowid()").fetchone()[0]
        return {"id": sid, "message": "Script created"}
    finally:
        db.close()


@router.put("/{script_id}")
def update_script(script_id: int, data: dict, user: TokenData = Depends(get_current_user)):
    """Admin: Update a trading script."""
    if not is_admin(user.user_id):
        raise HTTPException(403, "Admin only")
    db = get_db()
    try:
        updates = []
        params = []
        for k in ["name", "description", "symbol", "timeframe", "is_active"]:
            if k in data:
                updates.append(f"{k}=?")
                params.append(data[k])
        if "script_config" in data:
            updates.append("script_config=?")
            params.append(json.dumps(data["script_config"]))
        if not updates:
            raise HTTPException(400, "No fields to update")
        params.append(script_id)
        db.execute(f"UPDATE trading_scripts SET {', '.join(updates)}, updated_at=? WHERE id=?", 
                   (*params, datetime.utcnow().isoformat()))
        db.commit()
        return {"message": "Script updated"}
    finally:
        db.close()


@router.delete("/{script_id}")
def delete_script(script_id: int, user: TokenData = Depends(get_current_user)):
    """Admin: Delete a trading script."""
    if not is_admin(user.user_id):
        raise HTTPException(403, "Admin only")
    db = get_db()
    try:
        db.execute("DELETE FROM user_scripts WHERE script_id=?", (script_id,))
        db.execute("DELETE FROM trading_scripts WHERE id=?", (script_id,))
        db.commit()
        return {"message": "Script deleted"}
    finally:
        db.close()


@router.post("/{script_id}/enable")
def enable_script(script_id: int, data: dict, user: TokenData = Depends(get_current_user)):
    """User: Enable/disable a script for your account."""
    db = get_db()
    try:
        script = db.execute("SELECT * FROM trading_scripts WHERE id=? AND is_active=1", (script_id,)).fetchone()
        if not script:
            raise HTTPException(404, "Script not found")
        
        enabled = data.get("enabled", True)
        existing = db.execute("SELECT * FROM user_scripts WHERE user_id=? AND script_id=?", 
                             (user.user_id, script_id)).fetchone()
        if existing:
            db.execute("UPDATE user_scripts SET is_enabled=?, custom_lot_size=?, custom_risk=? WHERE user_id=? AND script_id=?",
                      (1 if enabled else 0, data.get("lot_size", 0.01), data.get("risk", 1.0), user.user_id, script_id))
        else:
            db.execute("INSERT INTO user_scripts (user_id, script_id, is_enabled, custom_lot_size, custom_risk) VALUES (?,?,?,?,?)",
                      (user.user_id, script_id, 1 if enabled else 0, data.get("lot_size", 0.01), data.get("risk", 1.0)))
        db.commit()
        return {"message": f"Script {'enabled' if enabled else 'disabled'}"}
    finally:
        db.close()


@router.get("/signals")
def signal_history(user: TokenData = Depends(get_current_user), limit: int = Query(50, ge=1, le=200)):
    """Get recent script signals."""
    db = get_db()
    try:
        if is_admin(user.user_id):
            rows = db.execute("SELECT * FROM script_signals ORDER BY created_at DESC LIMIT ?", (limit,)).fetchall()
        else:
            rows = db.execute("SELECT * FROM script_signals WHERE user_id=? ORDER BY created_at DESC LIMIT ?",
                            (user.user_id, limit)).fetchall()
        return [dict(r) for r in rows]
    finally:
        db.close()


# ── Admin APIs ──────────────────────────────────────────────────────────

@router.get("/admin/users")
def admin_users(user: TokenData = Depends(get_current_user)):
    """Admin: List all users with their script and trade stats."""
    if not is_admin(user.user_id):
        raise HTTPException(403, "Admin only")
    db = get_db()
    try:
        users = db.execute("SELECT id, username, email, full_name, created_at FROM users ORDER BY id").fetchall()
        result = []
        for u in users:
            ud = dict(u)
            ud["script_count"] = db.execute("SELECT COUNT(*) FROM user_scripts WHERE user_id=? AND is_enabled=1", (ud["id"],)).fetchone()[0]
            ud["trade_count"] = db.execute("SELECT COUNT(*) FROM trades WHERE user_id=?", (ud["id"],)).fetchone()[0]
            ud["signal_count"] = db.execute("SELECT COUNT(*) FROM script_signals WHERE user_id=?", (ud["id"],)).fetchone()[0]
            result.append(ud)
        return result
    finally:
        db.close()


@router.get("/admin/trades")
def admin_trades(user: TokenData = Depends(get_current_user), limit: int = Query(100, ge=1, le=500)):
    """Admin: View all trades across all users."""
    if not is_admin(user.user_id):
        raise HTTPException(403, "Admin only")
    db = get_db()
    try:
        rows = db.execute("""
            SELECT t.*, u.username FROM trades t 
            JOIN users u ON t.user_id = u.id 
            ORDER BY t.created_at DESC LIMIT ?
        """, (limit,)).fetchall()
        return [dict(r) for r in rows]
    finally:
        db.close()


@router.get("/admin/stats")
def admin_stats(user: TokenData = Depends(get_current_user)):
    """Admin: Get platform statistics."""
    if not is_admin(user.user_id):
        raise HTTPException(403, "Admin only")
    db = get_db()
    try:
        return {
            "total_users": db.execute("SELECT COUNT(*) FROM users").fetchone()[0],
            "total_scripts": db.execute("SELECT COUNT(*) FROM trading_scripts WHERE is_active=1").fetchone()[0],
            "active_scripts": db.execute("SELECT COUNT(DISTINCT script_id) FROM user_scripts WHERE is_enabled=1").fetchone()[0],
            "total_trades": db.execute("SELECT COUNT(*) FROM trades").fetchone()[0],
            "total_signals": db.execute("SELECT COUNT(*) FROM script_signals").fetchone()[0],
        }
    finally:
        db.close()
