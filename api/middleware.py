import time
from fastapi import Depends, HTTPException, status, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import JWTError, jwt
from config import JWT_SECRET, JWT_ALGORITHM

security = HTTPBearer()

_rate_limits: dict[str, list] = {}


def rate_limit_ip(request: Request, max_requests: int = 10, window: int = 60):
    ip = request.client.host if request.client else "unknown"
    now = time.time()
    if ip not in _rate_limits:
        _rate_limits[ip] = []
    _rate_limits[ip] = [t for t in _rate_limits[ip] if now - t < window]
    if len(_rate_limits[ip]) >= max_requests:
        raise HTTPException(status_code=429, detail="Too many requests. Please try again later.")
    _rate_limits[ip].append(now)


class TokenData:
    def __init__(self, username: str, user_id: int):
        self.username = username
        self.user_id = user_id


def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)) -> TokenData:
    exc = HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")
    try:
        payload = jwt.decode(credentials.credentials, JWT_SECRET, algorithms=[JWT_ALGORITHM])
        username = payload.get("sub")
        user_id = payload.get("user_id")
        if not username or not user_id:
            raise exc
        return TokenData(username=username, user_id=user_id)
    except JWTError:
        raise exc
