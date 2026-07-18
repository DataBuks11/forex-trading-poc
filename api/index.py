import os
import sys
sys.path.insert(0, os.path.dirname(__file__))

from fastapi import FastAPI, Request
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
async def quick_register(request: Request):
    try:
        data = await request.json()
        username = data.get("username", "demo")
        password = data.get("password", "demo123")
        from database import get_db
        db = get_db()
        db.execute("INSERT OR IGNORE INTO users (username, hashed_password) VALUES (?,?)", (username, "test_hash"))
        db.commit()
        user = db.execute("SELECT id, username FROM users WHERE username=?", (username,)).fetchone()
        db.close()
        return {"access_token": "dummy-token", "token_type": "bearer", "user": {"id": user["id"] if user else 1, "username": username}}
    except Exception as e:
        import traceback
        return {"error": str(e), "trace": traceback.format_exc().split("\n")[-5:]}

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
