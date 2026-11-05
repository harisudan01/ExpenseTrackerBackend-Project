from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, DeclarativeBase

from app.core.config import settings


# Create PostgreSQL engine
engine = create_engine(
    settings.DATABASE_URL,
    pool_pre_ping=True
)


# Create database sessions
SessionLocal = sessionmaker(
    bind=engine,
    autoflush=False,
    autocommit=False
)


# Base class for SQLAlchemy models
class Base(DeclarativeBase):
    pass


# Database dependency
def get_db():
    db = SessionLocal()

    try:
        yield db
    finally:
        db.close()