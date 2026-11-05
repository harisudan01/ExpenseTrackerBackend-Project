from fastapi import HTTPException, status
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.security import DUMMY_HASH, create_access_token, hash_password, verify_password
from app.repositories.user_repository import UserRepository
from app.schemas.auth_schema import LoginRequest, SignupRequest


class AuthService:

    def __init__(self):
        self.repository = UserRepository()

    def _auth_response(self, user):
        return {"access_token": create_access_token(user.id), "token_type": "bearer", "user": user}

    def signup(self, db: Session, data: SignupRequest):
        if self.repository.get_by_email(db, data.email):
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="An account with this email already exists"
            )

        is_first_user = self.repository.count(db) == 0

        try:
            user = self.repository.create(
                db,
                name=data.name,
                email=data.email,
                password_hash=hash_password(data.password),
                claim_unowned_books=is_first_user,
            )
        except IntegrityError:
            # Two sign-ups with the same email at the same moment
            db.rollback()
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="An account with this email already exists"
            )

        return self._auth_response(user)

    def login(self, db: Session, data: LoginRequest):
        user = self.repository.get_by_email(db, data.email)

        # Always run a bcrypt check so response time doesn't reveal whether the email exists
        password_ok = verify_password(data.password, user.password_hash if user else DUMMY_HASH)

        if not user or not password_ok:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Incorrect email or password"
            )

        return self._auth_response(user)
