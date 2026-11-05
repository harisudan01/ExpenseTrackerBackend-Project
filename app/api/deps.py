from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from app.core.security import decode_access_token
from app.database.connection import get_db
from app.models import User
from app.repositories.user_repository import UserRepository

bearer_scheme = HTTPBearer(auto_error=False)
user_repository = UserRepository()


def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
    db: Session = Depends(get_db),
) -> User:
    """Logged-in user from the `Authorization: Bearer <token>` header, or 401."""
    unauthorized = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Your session has expired. Please sign in again.",
        headers={"WWW-Authenticate": "Bearer"},
    )

    if not credentials:
        raise unauthorized

    user_id = decode_access_token(credentials.credentials)
    user = user_repository.get_by_id(db, user_id) if user_id else None

    if not user:
        raise unauthorized

    return user
