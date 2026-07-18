from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import JWTError, jwt
from config import JWT_SECRET, JWT_ALGORITHM

security = HTTPBearer()


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
