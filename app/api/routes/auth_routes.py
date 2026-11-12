from fastapi import APIRouter, BackgroundTasks, Depends, Request, Response, status
from sqlalchemy.orm import Session

from app.api.deps import (
    clear_session_cookie,
    get_current_user,
    set_session_cookie,
    user_from_session_token,
    user_repository,
)
from app.core.config import settings
from app.core.rate_limit import (
    account_key,
    client_ip,
    enforce,
    forgot_account_limiter,
    forgot_ip_limiter,
    login_account_limiter,
    login_ip_limiter,
    reset_ip_limiter,
    signup_ip_limiter,
)
from app.database.connection import get_db
from app.models import User
from app.schemas.auth_schema import (
    AuthResponse,
    ForgotPasswordRequest,
    LoginRequest,
    MessageResponse,
    ResetPasswordRequest,
    SignupRequest,
    UserResponse,
)
from app.services.auth_service import AuthService


router = APIRouter(
    prefix="/api/auth",
    tags=["Auth"]
)

service = AuthService()


# Create an account and log in
@router.post("/signup", response_model=AuthResponse, status_code=status.HTTP_201_CREATED)
def signup(data: SignupRequest, request: Request, response: Response, db: Session = Depends(get_db)):
    enforce(signup_ip_limiter, client_ip(request))
    user = service.signup(db, data)
    set_session_cookie(response, user)
    return {"user": user}


# Log in with email or username + password
@router.post("/login", response_model=AuthResponse)
def login(data: LoginRequest, request: Request, response: Response, db: Session = Depends(get_db)):
    enforce(login_ip_limiter, client_ip(request))
    enforce(login_account_limiter, account_key(data.identifier))
    user = service.login(db, data)
    set_session_cookie(response, user)
    return {"user": user}


# Log out: cancels every login token of the user (on all devices) and removes the cookie.
# Always succeeds, so it also clears a cookie that has already expired.
@router.post("/logout", response_model=MessageResponse)
def logout(request: Request, response: Response, db: Session = Depends(get_db)):
    user = user_from_session_token(db, request.cookies.get(settings.SESSION_COOKIE_NAME))
    if user:
        user_repository.revoke_tokens(db, user)
    clear_session_cookie(response)
    return {"message": "You have been signed out."}


# Email a password reset link (same reply whether or not the account exists)
@router.post("/forgot-password", response_model=MessageResponse)
def forgot_password(
    data: ForgotPasswordRequest, request: Request, background: BackgroundTasks, db: Session = Depends(get_db)
):
    enforce(forgot_ip_limiter, client_ip(request))
    enforce(forgot_account_limiter, account_key(data.identifier))
    return service.forgot_password(db, data, background)


# Set a new password using the token from the reset link
@router.post("/reset-password", response_model=MessageResponse)
def reset_password(data: ResetPasswordRequest, request: Request, db: Session = Depends(get_db)):
    enforce(reset_ip_limiter, client_ip(request))
    return service.reset_password(db, data)


# Currently logged-in user
@router.get("/me", response_model=UserResponse)
def me(user: User = Depends(get_current_user)):
    return user
