from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(title="Forex POC API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/api/health")
def health():
    return {"status": "ok", "version": "2.0.0"}

@app.get("/api/auth/register")
def quick_register(username: str = "demo", password: str = "demo123"):
    import hashlib, os
    from database import get_db
    db = get_db()
    try:
        salt = os.urandom(32).hex()
        pwd = hashlib.pbkdf2_hmac("sha256", password.encode(), salt.encode(), 100000).hex()
        hashed = f"{salt}${pwd}"
        db.execute("INSERT OR IGNORE INTO users (username, hashed_password) VALUES (?,?)", (username, hashed))
        db.commit()
        from datetime import datetime, timedelta
        from jose import jwt
        user = db.execute("SELECT id, username FROM users WHERE username=?", (username,)).fetchone()
        token = jwt.encode(
            {"sub": username, "user_id": user["id"], "exp": datetime.utcnow() + timedelta(days=1)},
            "forex-poc-demo-secret-key-2024",
            algorithm="HS256"
        )
        return {"access_token": token, "token_type": "bearer", "user": {"id": user["id"], "username": user["username"]}}
    finally:
        db.close()

@app.get("/api/dashboard")
def dashboard():
    from database import get_db
    db = get_db()
    try:
        return {"account": None, "open_positions": [], "trade_history": [], "recent_activity": [], "stats": {}}
    finally:
        db.close()
