import hashlib
import hmac
from datetime import datetime, timedelta, timezone

import bcrypt
import jwt

from app.core.config import settings


# ---------- passwords ----------

def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")


def verify_password(password: str, password_hash: str) -> bool:
    try:
        return bcrypt.checkpw(password.encode("utf-8"), password_hash.encode("utf-8"))
    except ValueError:
        # Malformed hash, or a password over bcrypt's 72-byte limit
        return False


# Used when the email doesn't exist, so a failed login takes the same time either way
DUMMY_HASH = hash_password("timing-equaliser")


# ---------- tokens ----------

def create_access_token(user_id: int) -> str:
    now = datetime.now(timezone.utc)
    payload = {
        "sub": str(user_id),
        "iat": now,
        "exp": now + timedelta(minutes=settings.JWT_EXPIRE_MINUTES),
    }
    return jwt.encode(payload, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM)


def decode_access_token(token: str) -> int | None:
    """User id from a valid token, or None if it is invalid / expired."""
    try:
        payload = jwt.decode(
            token, settings.JWT_SECRET_KEY, algorithms=[settings.JWT_ALGORITHM]
        )
        return int(payload["sub"])
    except (jwt.PyJWTError, KeyError, ValueError):
        return None


# ---------- password reset tokens ----------
# Signed with a separate key so a reset token can never be used as a login token (and vice versa).
# Each token carries a fingerprint of the current password hash, so it stops working as soon as
# the password changes: a link can only be used once, and older links die after a reset.

_RESET_PURPOSE = "password_reset"


def _reset_key() -> str:
    return settings.JWT_SECRET_KEY + ":" + _RESET_PURPOSE


def _password_fingerprint(password_hash: str) -> str:
    return hashlib.sha256(password_hash.encode("utf-8")).hexdigest()[:32]


def create_password_reset_token(user_id: int, password_hash: str) -> str:
    now = datetime.now(timezone.utc)
    payload = {
        "sub": str(user_id),
        "purpose": _RESET_PURPOSE,
        "pwd": _password_fingerprint(password_hash),
        "iat": now,
        "exp": now + timedelta(minutes=settings.PASSWORD_RESET_EXPIRE_MINUTES),
    }
    return jwt.encode(payload, _reset_key(), algorithm=settings.JWT_ALGORITHM)


def decode_password_reset_token(token: str) -> tuple[int, str] | None:
    """(user id, password fingerprint) from a valid reset token, or None."""
    try:
        payload = jwt.decode(token, _reset_key(), algorithms=[settings.JWT_ALGORITHM])
        if payload.get("purpose") != _RESET_PURPOSE:
            return None
        return int(payload["sub"]), str(payload["pwd"])
    except (jwt.PyJWTError, KeyError, ValueError):
        return None


def password_fingerprint_matches(password_hash: str, fingerprint: str) -> bool:
    return hmac.compare_digest(_password_fingerprint(password_hash), fingerprint)
