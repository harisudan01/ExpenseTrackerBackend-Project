from datetime import datetime

from sqlalchemy import BigInteger, Integer, String, DateTime, func
from sqlalchemy.orm import Mapped, mapped_column

from app.database.connection import Base


class User(Base):
    __tablename__ = "cashexpense_users"

    # BIGINT in PostgreSQL; INTEGER in SQLite so ids are auto-numbered
    id: Mapped[int] = mapped_column(BigInteger().with_variant(Integer, "sqlite"), primary_key=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    # Stored lower-cased so lookups are case-insensitive
    email: Mapped[str] = mapped_column(String(255), nullable=False, unique=True, index=True)
    # Lower-cased too; NULL only for accounts created before usernames existed
    username: Mapped[str | None] = mapped_column(String(30), nullable=True, unique=True, index=True)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
