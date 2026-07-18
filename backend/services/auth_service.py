from datetime import datetime, timedelta
from jose import jwt
from config import JWT_SECRET, JWT_ALGORITHM, JWT_EXPIRE_MINUTES
from repositories.user_repo import (
    create_user, get_user_by_username, get_user_by_email,
    verify_password, save_reset_token,
)
from repositories.activity_repo import log_activity
from repositories.settings_repo import get_settings
import secrets


def register_user(username: str, password: str, email: str = "", full_name: str = "") -> dict:
    user = create_user(username, password, email, full_name)
    if not user:
        raise ValueError("Username already exists")
    get_settings(user["id"])
    log_activity(user["id"], "user_registered", f"User '{username}' registered")
    token = create_access_token({"sub": username, "user_id": user["id"]})
    return {"access_token": token, "token_type": "bearer", "user": sanitize_user(user)}


def login_user(username: str, password: str) -> dict:
    user = get_user_by_username(username)
    if not user or not verify_password(password, user["hashed_password"]):
        raise ValueError("Invalid credentials")
    log_activity(user["id"], "user_login", f"User '{username}' logged in")
    token = create_access_token({"sub": username, "user_id": user["id"]})
    return {"access_token": token, "token_type": "bearer", "user": sanitize_user(user)}


def forgot_password(email: str) -> bool:
    user = get_user_by_email(email)
    if not user:
        return True
    token = secrets.token_urlsafe(32)
    save_reset_token(user["id"], token)
    log_activity(user["id"], "password_reset_requested", f"Reset requested for {email}")
    return True


def create_access_token(data: dict) -> str:
    to_encode = data.copy()
    to_encode["exp"] = datetime.utcnow() + timedelta(minutes=JWT_EXPIRE_MINUTES)
    return jwt.encode(to_encode, JWT_SECRET, algorithm=JWT_ALGORITHM)


def sanitize_user(user: dict) -> dict:
    return {
        "id": user["id"],
        "username": user["username"],
        "email": user.get("email", ""),
        "full_name": user.get("full_name", ""),
        "created_at": user.get("created_at", ""),
    }
