import os

JWT_SECRET = os.environ.get("JWT_SECRET", "forex-poc-demo-secret-key-2024")
JWT_ALGORITHM = "HS256"
JWT_EXPIRE_MINUTES = 1440

MT5_DEV = 20
MT5_MAGIC = 123456
MT5_TIMEOUT = 10000

_cors_env = os.environ.get("CORS_ORIGINS", "")
_cors_default = ["http://localhost:3000", "http://127.0.0.1:3000"]
CORS_ORIGINS = [o.strip() for o in _cors_env.split(",") if o.strip()] if _cors_env else _cors_default
