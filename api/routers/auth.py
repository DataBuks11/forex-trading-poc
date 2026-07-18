from fastapi import APIRouter, HTTPException, Depends
from schemas.auth import LoginRequest, RegisterRequest, TokenResponse, ForgotPasswordRequest
from services.auth_service import register_user, login_user, forgot_password
from middleware import get_current_user, TokenData

router = APIRouter(prefix="/api/auth", tags=["Authentication"])


@router.post("/register")
def register(payload: RegisterRequest):
    """Register a new user account. Returns JWT token on success."""
    try:
        result = register_user(payload.username, payload.password,
                               payload.email, payload.full_name)
        return result
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/login", response_model=TokenResponse)
def login(payload: LoginRequest):
    """Login with username and password. Returns JWT token."""
    try:
        result = login_user(payload.username, payload.password)
        return result
    except ValueError as e:
        raise HTTPException(status_code=401, detail=str(e))


@router.get("/me")
def me(current_user: TokenData = Depends(get_current_user)):
    """Get current authenticated user profile."""
    from repositories.user_repo import get_user_by_id
    user = get_user_by_id(current_user.user_id)
    if not user:
        raise HTTPException(404, "User not found")
    return {
        "id": user["id"], "username": user["username"],
        "email": user.get("email", ""), "full_name": user.get("full_name", ""),
        "created_at": user.get("created_at", ""),
    }


@router.post("/forgot-password")
def forgot_pw(payload: ForgotPasswordRequest):
    """Request a password reset. (Demo: always returns success for security)."""
    forgot_password(payload.email)
    return {"message": "If the email exists, a reset link has been sent."}
