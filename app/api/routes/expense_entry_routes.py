from datetime import date

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.database.connection import get_db
from app.models import User
from app.schemas.expense_entry_schema import (
    ExpenseEntryCreate,
    ExpenseEntryUpdate,
    ExpenseEntryResponse,
    ExpenseEntrySummary,
    TransactionType
)
from app.services.expense_entry_service import ExpenseEntryService


# Every route needs a logged-in user, and only reaches entries of that user's books
router = APIRouter(
    prefix="/api",
    tags=["Expense Entries"]
)

service = ExpenseEntryService()


# Get all entries of a book (optional filters)
@router.get(
    "/books/{book_id}/entries",
    response_model=list[ExpenseEntryResponse]
)
def get_entries(
    book_id: int,
    transaction_type: TransactionType | None = Query(default=None),
    start_date: date | None = Query(default=None),
    end_date: date | None = Query(default=None),
    search: str | None = Query(default=None, max_length=100),
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user)
):
    return service.get_entries(
        db, book_id, user.id, transaction_type, start_date, end_date, search
    )


# Cash in / cash out / net balance of a book
@router.get(
    "/books/{book_id}/entries/summary",
    response_model=ExpenseEntrySummary
)
def get_summary(
    book_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user)
):
    return service.get_summary(db, book_id, user.id)


# Create entry in a book
@router.post(
    "/books/{book_id}/entries",
    response_model=ExpenseEntryResponse,
    status_code=status.HTTP_201_CREATED
)
def create_entry(
    book_id: int,
    entry_data: ExpenseEntryCreate,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user)
):
    return service.create_entry(db, book_id, entry_data, user.id)


# Get entry by ID
@router.get("/entries/{entry_id}", response_model=ExpenseEntryResponse)
def get_entry(
    entry_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user)
):
    return service.get_entry(db, entry_id, user.id)


# Update entry
@router.put("/entries/{entry_id}", response_model=ExpenseEntryResponse)
def update_entry(
    entry_id: int,
    entry_data: ExpenseEntryUpdate,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user)
):
    return service.update_entry(db, entry_id, entry_data, user.id)


# Delete entry
@router.delete("/entries/{entry_id}")
def delete_entry(
    entry_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user)
):
    return service.delete_entry(db, entry_id, user.id)
