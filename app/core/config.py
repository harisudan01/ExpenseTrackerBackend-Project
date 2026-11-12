import logging
import secrets
from pathlib import Path
from typing import Literal

from pydantic_settings import BaseSettings, SettingsConfigDict

logger = logging.getLogger("app.config")


class Settings(BaseSettings):

    APP_NAME: str = "Expense Tracker API"

    # PostgreSQL connection string, e.g. postgresql+psycopg://USER:PASSWORD@HOST:5432/postgres
    # If empty, a built-in SQLite database is created in DATA_DIR, so the app (and the Docker image)
    # runs with no setup at all. That database starts empty.
    DATABASE_URL: str = ""

    # Where the built-in SQLite database and the generated JWT secret are stored
    # (/app/data in the Docker image; mount a volume there to keep them).
    DATA_DIR: str = "data"

    # Frontend origins allowed to call the API.
    # Override in .env as JSON, e.g. CORS_ORIGINS=["https://myapp.vercel.app"]
    CORS_ORIGINS: list[str] = [
        "http://localhost:4200",
        "http://127.0.0.1:4200",
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://localhost:8080",
        "http://127.0.0.1:8080",
        "https://expense-trackegilt.vercel.app",
    ]

    # Secret used to sign login tokens. Set a long random value in .env for real deployments
    # (generate one with: python -c "import secrets; print(secrets.token_urlsafe(48))").
    # If empty, one is generated and saved in DATA_DIR.
    JWT_SECRET_KEY: str = ""
    JWT_ALGORITHM: str = "HS256"
    # How long a login lasts (default 1 day)
    JWT_EXPIRE_MINUTES: int = 60 * 24

    # ---------- session cookie ----------
    # The login token is kept in an HttpOnly cookie, so page scripts (and any XSS) can't read it.
    SESSION_COOKIE_NAME: str = "et_session"
    # Send the cookie over HTTPS only. Set false only for plain-http setups other than localhost
    # (e.g. docker compose opened from another machine); browsers allow Secure cookies on http://localhost.
    COOKIE_SECURE: bool = True
    # "strict": the cookie is never sent with requests started by other sites (CSRF protection).
    # Needs the frontend and API on the same site, e.g. the API proxied under the frontend's /api.
    COOKIE_SAMESITE: Literal["strict", "lax", "none"] = "strict"

    # ---------- forgot password ----------
    # Where the React app lives; the reset link in the email points here
    FRONTEND_URL: str = "http://localhost:5173"
    # How long a reset link stays valid
    PASSWORD_RESET_EXPIRE_MINUTES: int = 30

    # SMTP server used to send reset emails. If SMTP_HOST is empty, the reset link is
    # written to the server log instead (handy for local development).
    SMTP_HOST: str = ""
    SMTP_PORT: int = 587
    SMTP_USERNAME: str = ""
    SMTP_PASSWORD: str = ""
    SMTP_FROM: str = ""
    # STARTTLS on port 587; set SMTP_USE_SSL=true instead for port 465
    SMTP_USE_TLS: bool = True
    SMTP_USE_SSL: bool = False

    # ---------- security ----------
    # Limit login / signup / password-reset attempts (see app/core/rate_limit.py)
    RATE_LIMIT_ENABLED: bool = True
    # Serve the interactive API docs at /docs, /redoc and /openapi.json.
    # Off by default so production doesn't publish a map of the API; set true for local development.
    ENABLE_API_DOCS: bool = False

    model_config = SettingsConfigDict(
        env_file=".env",
        extra="ignore"
    )

    @property
    def using_builtin_database(self) -> bool:
        return self.DATABASE_URL.startswith("sqlite")


def _load_settings() -> Settings:
    s = Settings()
    data_dir = Path(s.DATA_DIR)

    if not s.DATABASE_URL:
        data_dir.mkdir(parents=True, exist_ok=True)
        s.DATABASE_URL = f"sqlite:///{(data_dir / 'expense_tracker.db').resolve().as_posix()}"
        logger.warning(
            "DATABASE_URL is not set: using the built-in SQLite database at %s (starts empty). "
            "Set DATABASE_URL to use PostgreSQL.", s.DATABASE_URL
        )

    if not s.JWT_SECRET_KEY:
        # Saved to a file so logins survive a restart
        data_dir.mkdir(parents=True, exist_ok=True)
        key_file = data_dir / "jwt_secret"
        if key_file.exists():
            s.JWT_SECRET_KEY = key_file.read_text(encoding="utf-8").strip()
        else:
            s.JWT_SECRET_KEY = secrets.token_urlsafe(48)
            key_file.write_text(s.JWT_SECRET_KEY, encoding="utf-8")
            key_file.chmod(0o600)
        logger.warning("JWT_SECRET_KEY is not set: using a generated key stored in %s", key_file)

    return s


settings = _load_settings()
