from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.database.connection import get_db
from app.models import User
from app.schemas.expense_book_schema import (
    ExpenseBookCreate,
    ExpenseBookUpdate,
    ExpenseBookReorder,
    ExpenseBookResponse
)
from app.services.expense_book_service import ExpenseBookService


# Every route needs a logged-in user, and only sees that user's books
router = APIRouter(
    prefix="/api/books",
    tags=["Expense Books"]
)

service = ExpenseBookService()


# Get all expense books
@router.get("", response_model=list[ExpenseBookResponse])
def get_all_books(
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user)
):
    return service.get_all_books(db, user.id)


# Save drag and drop order
# (declared before "/{book_id}" so "reorder" is not parsed as an ID)
@router.put("/reorder", response_model=list[ExpenseBookResponse])
def reorder_books(
    payload: ExpenseBookReorder,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user)
):
    return service.reorder_books(db, payload.book_ids, user.id)


# Get expense book by ID
@router.get("/{book_id}", response_model=ExpenseBookResponse)
def get_book(
    book_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user)
):
    return service.get_book(db, book_id, user.id)


# Create expense book
@router.post(
    "",
    response_model=ExpenseBookResponse,
    status_code=status.HTTP_201_CREATED
)
def create_book(
    book_data: ExpenseBookCreate,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user)
):
    return service.create_book(db, book_data, user.id)


# Update expense book
@router.put("/{book_id}", response_model=ExpenseBookResponse)
def update_book(
    book_id: int,
    book_data: ExpenseBookUpdate,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user)
):
    return service.update_book(db, book_id, book_data, user.id)


# Delete expense book
@router.delete("/{book_id}")
def delete_book(
    book_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user)
):
    return service.delete_book(db, book_id, user.id)
