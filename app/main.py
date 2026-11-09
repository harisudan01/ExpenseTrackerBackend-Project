from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import text
from sqlalchemy.orm import Session


from app.core.config import settings
from app.database.connection import Base, engine, get_db
from app.api.routes import auth_router, expense_book_router, expense_entry_router

# The built-in SQLite database is created from the models (the SQL files in /migrations are for PostgreSQL)
if settings.using_builtin_database:
    from app import models as _models  # noqa: F401  registers every table on Base
    Base.metadata.create_all(bind=engine)

app = FastAPI(
    title=settings.APP_NAME,
    version="1.0.0"
)

# Allow the Angular / React frontends to call this API
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        *settings.CORS_ORIGINS,
        "https://expense-trackegilt.vercel.app",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth_router)
app.include_router(expense_book_router)
app.include_router(expense_entry_router)


@app.get("/")
def root():
    return {
        "message": "Expense Tracker API is running!"
    }


@app.get("/health")
def health_check():
    return {
        "status": "healthy"
    }


@app.get("/health/database")
def database_health(db: Session = Depends(get_db)):
    db.execute(text("SELECT 1"))

    return {
        "status": "connected",
        "database": "Built-in SQLite" if settings.using_builtin_database else "PostgreSQL"
    }
