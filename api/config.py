import os

JWT_SECRET = os.environ.get("JWT_SECRET", "forex-trading-prod-secret-change-me")
JWT_ALGORITHM = "HS256"
JWT_EXPIRE_MINUTES = 1440

MT5_DEV = 20
MT5_MAGIC = 123456
MT5_TIMEOUT = 10000

_cors_env = os.environ.get("CORS_ORIGINS", "")
_cors_default = [
    "https://frontend-fawn-omega-29.vercel.app",
    "http://localhost:3000",
    "http://127.0.0.1:3000",
]
CORS_ORIGINS = [o.strip() for o in _cors_env.split(",") if o.strip()] if _cors_env else _cors_default

MAX_LOT_SIZE = float(os.environ.get("MAX_LOT_SIZE", "10.0"))
API_DOMAIN = os.environ.get("API_DOMAIN", "api-woad-ten-44.vercel.app")
