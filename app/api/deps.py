from fastapi import Depends, HTTPException, Request, Response, status
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.security import create_access_token, decode_access_token
from app.database.connection import get_db
from app.models import User
from app.repositories.user_repository import UserRepository

user_repository = UserRepository()

# The cookie is only sent to the API, never with page or asset requests
SESSION_COOKIE_PATH = "/api"


def user_from_session_token(db: Session, token: str | None) -> User | None:
    """The user a session token belongs to, or None if it is invalid, expired or cancelled."""
    decoded = decode_access_token(token) if token else None
    if not decoded:
        return None
    user_id, token_version = decoded
    user = user_repository.get_by_id(db, user_id)
    # A logout or password reset increases token_version, which cancels every older token
    if not user or user.token_version != token_version:
        return None
    return user


def get_current_user(request: Request, db: Session = Depends(get_db)) -> User:
    """Logged-in user from the HttpOnly session cookie, or 401."""
    user = user_from_session_token(db, request.cookies.get(settings.SESSION_COOKIE_NAME))
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Your session has expired. Please sign in again.",
        )
    return user


def set_session_cookie(response: Response, user: User) -> None:
    response.set_cookie(
        key=settings.SESSION_COOKIE_NAME,
        value=create_access_token(user.id, user.token_version),
        max_age=settings.JWT_EXPIRE_MINUTES * 60,
        path=SESSION_COOKIE_PATH,
        httponly=True,
        secure=settings.COOKIE_SECURE,
        samesite=settings.COOKIE_SAMESITE,
    )


def clear_session_cookie(response: Response) -> None:
    response.delete_cookie(
        key=settings.SESSION_COOKIE_NAME,
        path=SESSION_COOKIE_PATH,
        httponly=True,
        secure=settings.COOKIE_SECURE,
        samesite=settings.COOKIE_SAMESITE,
    )
