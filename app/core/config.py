from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):

    APP_NAME: str = "Expense Tracker API"

    DATABASE_URL: str

    # Frontend origins allowed to call the API.
    # Override in .env as JSON, e.g. CORS_ORIGINS=["https://myapp.vercel.app"]
    CORS_ORIGINS: list[str] = [
        "http://localhost:4200",
        "http://127.0.0.1:4200",
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "https://expense-trackegilt.vercel.app",
    ]

    # Secret used to sign login tokens. Required: set a long random value in .env
    # (generate one with: python -c "import secrets; print(secrets.token_urlsafe(48))")
    JWT_SECRET_KEY: str
    JWT_ALGORITHM: str = "HS256"
    # How long a login lasts (default 7 days)
    JWT_EXPIRE_MINUTES: int = 60 * 24 * 7

    model_config = SettingsConfigDict(
        env_file=".env",
        extra="ignore"
    )


settings = Settings()
