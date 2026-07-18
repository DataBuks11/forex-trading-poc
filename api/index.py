import os
import sys
sys.path.insert(0, os.path.dirname(__file__))

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

@app.post("/api/quick-register")
def quick_register(data: dict):
    import hashlib, secrets
    from database import get_db
    username = data.get("username", "demo")
    password = data.get("password", "demo123")
    db = get_db()
    try:
        salt = secrets.token_hex(16)
        pwd = hashlib.pbkdf2_hmac("sha256", password.encode(), salt.encode(), 100000).hex()
        hashed = f"{salt}${pwd}"
        db.execute("INSERT OR IGNORE INTO users (username, hashed_password) VALUES (?,?)", (username, hashed))
        db.commit()
        user = db.execute("SELECT id, username FROM users WHERE username=?", (username,)).fetchone()
        if not user:
            user = {"id": 1, "username": username}
        from datetime import datetime, timedelta
        from jose import jwt
        token = jwt.encode(
            {"sub": username, "user_id": user["id"], "exp": datetime.utcnow() + timedelta(days=1)},
            "forex-poc-demo-secret-2024", algorithm="HS256"
        )
        return {"access_token": token, "token_type": "bearer", "user": {"id": user["id"], "username": username}}
    except Exception as e:
        return {"error": str(e)}
    finally:
        db.close()

# Now import and register all routes
try:
    from database import init_db
    init_db()
except Exception as e:
    pass

try:
    from routers.auth import router as auth_router
    app.include_router(auth_router)
except Exception as e:
    pass

try:
    from routers.mt5 import router as mt5_router
    app.include_router(mt5_router)
except Exception as e:
    pass

try:
    from routers.dashboard import router as dashboard_router
    app.include_router(dashboard_router)
except Exception as e:
    pass

try:
    from routers.webhook import router as webhook_router
    app.include_router(webhook_router)
except Exception as e:
    pass

try:
    from routers.trades import router as trades_router
    app.include_router(trades_router)
except Exception as e:
    pass

try:
    from routers.activity import router as activity_router
    app.include_router(activity_router)
except Exception as e:
    pass

try:
    from routers.settings import router as settings_router
    app.include_router(settings_router)
except Exception as e:
    pass
