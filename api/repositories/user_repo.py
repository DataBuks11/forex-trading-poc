from database import get_db
import hashlib
import os


def hash_password(password: str) -> str:
    salt = os.urandom(32).hex()
    pwdhash = hashlib.pbkdf2_hmac("sha256", password.encode(), salt.encode(), 100000).hex()
    return f"{salt}${pwdhash}"


def verify_password(plain: str, hashed: str) -> bool:
    try:
        salt, pwdhash = hashed.split("$")
        return pwdhash == hashlib.pbkdf2_hmac("sha256", plain.encode(), salt.encode(), 100000).hex()
    except Exception:
        return False


def create_user(username: str, password: str, email: str = "", full_name: str = "") -> dict | None:
    db = get_db()
    try:
        hashed = hash_password(password)
        db.execute(
            "INSERT INTO users (username, email, hashed_password, full_name) VALUES (?,?,?,?)",
            (username, email, hashed, full_name),
        )
        db.commit()
        row = db.execute("SELECT * FROM users WHERE username=?", (username,)).fetchone()
        return dict(row) if row else None
    except Exception:
        return None
    finally:
        db.close()


def get_user_by_username(username: str) -> dict | None:
    db = get_db()
    try:
        row = db.execute("SELECT * FROM users WHERE username=?", (username,)).fetchone()
        return dict(row) if row else None
    finally:
        db.close()


def get_user_by_id(user_id: int) -> dict | None:
    db = get_db()
    try:
        row = db.execute("SELECT * FROM users WHERE id=?", (user_id,)).fetchone()
        return dict(row) if row else None
    finally:
        db.close()


def get_user_by_email(email: str) -> dict | None:
    db = get_db()
    try:
        row = db.execute("SELECT * FROM users WHERE email=?", (email,)).fetchone()
        return dict(row) if row else None
    finally:
        db.close()


def save_reset_token(user_id: int, token: str) -> bool:
    db = get_db()
    try:
        from datetime import datetime, timedelta
        expires = datetime.utcnow() + timedelta(hours=1)
        db.execute(
            "INSERT INTO password_reset_tokens (user_id, token, expires_at) VALUES (?,?,?)",
            (user_id, token, expires.isoformat()),
        )
        db.commit()
        return True
    except Exception:
        return False
    finally:
        db.close()
