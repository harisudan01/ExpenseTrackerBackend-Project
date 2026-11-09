from html import escape
from urllib.parse import quote

from fastapi import BackgroundTasks, HTTPException, status
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.email import send_email
from app.core.security import (
    DUMMY_HASH,
    create_access_token,
    create_password_reset_token,
    decode_password_reset_token,
    hash_password,
    password_fingerprint_matches,
    verify_password,
)
from app.repositories.user_repository import UserRepository
from app.schemas.auth_schema import ForgotPasswordRequest, LoginRequest, ResetPasswordRequest, SignupRequest


# Same reply whether or not the account exists, so this can't be used to discover accounts
FORGOT_PASSWORD_MESSAGE = (
    "If an account matches what you entered, we've sent a password reset link to its email address."
)


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
        if self.repository.get_by_username(db, data.username):
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="This username is already taken"
            )

        is_first_user = self.repository.count(db) == 0

        try:
            user = self.repository.create(
                db,
                name=data.name,
                email=data.email,
                username=data.username,
                password_hash=hash_password(data.password),
                claim_unowned_books=is_first_user,
            )
        except IntegrityError:
            # Two sign-ups with the same email or username at the same moment
            db.rollback()
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="An account with this email or username already exists"
            )

        return self._auth_response(user)

    def login(self, db: Session, data: LoginRequest):
        user = self.repository.get_by_login(db, data.identifier)

        # Always run a bcrypt check so response time doesn't reveal whether the account exists
        password_ok = verify_password(data.password, user.password_hash if user else DUMMY_HASH)

        if not user or not password_ok:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Incorrect email/username or password"
            )

        return self._auth_response(user)

    def forgot_password(self, db: Session, data: ForgotPasswordRequest, background: BackgroundTasks):
        user = self.repository.get_by_login(db, data.identifier)
        if user:
            token = create_password_reset_token(user.id, user.password_hash)
            link = f"{settings.FRONTEND_URL.rstrip('/')}/reset-password?token={quote(token)}"
            minutes = settings.PASSWORD_RESET_EXPIRE_MINUTES
            text = (
                f"Hi {user.name},\n\n"
                f"We received a request to reset your Expense Tracker password.\n"
                f"Open this link to choose a new one (valid for {minutes} minutes):\n\n"
                f"{link}\n\n"
                f"If you didn't ask for this, you can ignore this email; your password won't change."
            )
            html = (
                f"<p>Hi {escape(user.name)},</p>"
                f"<p>We received a request to reset your Expense Tracker password.</p>"
                f'<p><a href="{escape(link)}">Reset your password</a> (valid for {minutes} minutes)</p>'
                f"<p>If you didn't ask for this, you can ignore this email; your password won't change.</p>"
            )
            # Sent after the response, so timing doesn't reveal whether the account exists
            background.add_task(send_email, user.email, "Reset your Expense Tracker password", text, html)

        return {"message": FORGOT_PASSWORD_MESSAGE}

    def reset_password(self, db: Session, data: ResetPasswordRequest):
        invalid = HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="This reset link is invalid or has expired. Please request a new one."
        )

        decoded = decode_password_reset_token(data.token)
        if not decoded:
            raise invalid
        user_id, fingerprint = decoded

        user = self.repository.get_by_id(db, user_id)
        # The fingerprint no longer matches once the password has changed, so each link works once
        if not user or not password_fingerprint_matches(user.password_hash, fingerprint):
            raise invalid

        self.repository.set_password(db, user, hash_password(data.password))
        return {"message": "Your password has been reset. You can now sign in with your new password."}
