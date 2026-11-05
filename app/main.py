from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import text
from sqlalchemy.orm import Session


from app.core.config import settings
from app.database.connection import get_db
from app.api.routes import auth_router, expense_book_router, expense_entry_router

app = FastAPI(
    title=settings.APP_NAME,
    version="1.0.0"
)

# Allow the Angular / React frontends to call this API
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
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
        "database": "Supabase PostgreSQL"
    }
