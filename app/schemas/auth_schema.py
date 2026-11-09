import re
from datetime import datetime

from pydantic import AliasChoices, BaseModel, ConfigDict, EmailStr, Field, field_validator


# bcrypt only uses the first 72 bytes of a password
MAX_PASSWORD_BYTES = 72

# 3-30 characters: letters, numbers, "_" and ".", starting with a letter or number.
# No "@", so a login value can always be told apart from an email.
USERNAME_RE = re.compile(r"^[a-z0-9][a-z0-9_.]{2,29}$")


def check_password_rules(v: str) -> str:
    if len(v.encode("utf-8")) > MAX_PASSWORD_BYTES:
        raise ValueError("Password is too long (max 72 bytes)")
    if not any(c.isalpha() for c in v) or not any(c.isdigit() for c in v):
        raise ValueError("Password must contain at least one letter and one number")
    return v


class SignupRequest(BaseModel):
    name: str = Field(min_length=1, max_length=100)
    username: str = Field(min_length=3, max_length=30)
    email: EmailStr
    password: str = Field(min_length=8)

    @field_validator("name")
    @classmethod
    def name_not_blank(cls, v: str) -> str:
        v = v.strip()
        if not v:
            raise ValueError("Name cannot be empty")
        return v

    @field_validator("username")
    @classmethod
    def username_rules(cls, v: str) -> str:
        v = v.strip().lower()
        if not USERNAME_RE.match(v):
            raise ValueError(
                "Username must be 3-30 characters: letters, numbers, '_' or '.', starting with a letter or number"
            )
        return v

    @field_validator("password")
    @classmethod
    def password_rules(cls, v: str) -> str:
        return check_password_rules(v)


class LoginRequest(BaseModel):
    # Email or username. "email" is still accepted so older clients keep working.
    identifier: str = Field(
        min_length=1,
        max_length=255,
        validation_alias=AliasChoices("identifier", "email", "username"),
    )
    password: str = Field(min_length=1)


class ForgotPasswordRequest(BaseModel):
    # Email or username
    identifier: str = Field(min_length=1, max_length=255)


class ResetPasswordRequest(BaseModel):
    token: str = Field(min_length=1)
    password: str = Field(min_length=8)

    @field_validator("password")
    @classmethod
    def password_rules(cls, v: str) -> str:
        return check_password_rules(v)


class MessageResponse(BaseModel):
    message: str


class UserResponse(BaseModel):
    id: int
    name: str
    username: str | None = None
    email: str
    created_at: datetime | None = None

    model_config = ConfigDict(from_attributes=True)


class AuthResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserResponse
