from datetime import date

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.repositories.expense_book_repository import ExpenseBookRepository
from app.repositories.expense_entry_repository import ExpenseEntryRepository
from app.schemas.expense_entry_schema import (
    ExpenseEntryCreate,
    ExpenseEntryUpdate
)


class ExpenseEntryService:

    def __init__(self):
        self.repository = ExpenseEntryRepository()
        self.book_repository = ExpenseBookRepository()

    # The table has no foreign key, so check the book exists and is the user's
    def _ensure_book_exists(self, db: Session, book_id: int, user_id: int):
        if not self.book_repository.get_by_id(db, book_id, user_id):
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Expense book not found"
            )

    # Get all entries of a book
    def get_entries(
        self,
        db: Session,
        book_id: int,
        user_id: int,
        transaction_type: str | None = None,
        start_date: date | None = None,
        end_date: date | None = None,
        search: str | None = None
    ):
        self._ensure_book_exists(db, book_id, user_id)

        if start_date and end_date and start_date > end_date:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="start_date cannot be after end_date"
            )

        return self.repository.get_by_book(
            db, book_id, transaction_type, start_date, end_date, search
        )

    # Totals for a book
    def get_summary(self, db: Session, book_id: int, user_id: int):
        self._ensure_book_exists(db, book_id, user_id)

        total, cash_in, cash_out = self.repository.get_summary(db, book_id)

        return {
            "book_id": book_id,
            "total_entries": total,
            "cash_in": float(cash_in),
            "cash_out": float(cash_out),
            "net_balance": float(cash_in - cash_out)
        }

    # Get entry by ID (404 unless its book belongs to the user)
    def get_entry(self, db: Session, entry_id: int, user_id: int):
        entry = self.repository.get_by_id(db, entry_id)

        if not entry or not self.book_repository.get_by_id(db, entry.book_id, user_id):
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Expense entry not found"
            )

        return entry

    # Create entry
    def create_entry(
        self,
        db: Session,
        book_id: int,
        entry_data: ExpenseEntryCreate,
        user_id: int
    ):
        self._ensure_book_exists(db, book_id, user_id)

        return self.repository.create(db, book_id, entry_data)

    # Update entry
    def update_entry(
        self,
        db: Session,
        entry_id: int,
        entry_data: ExpenseEntryUpdate,
        user_id: int
    ):
        entry = self.get_entry(db, entry_id, user_id)

        return self.repository.update(db, entry, entry_data)

    # Delete entry
    def delete_entry(self, db: Session, entry_id: int, user_id: int):
        entry = self.get_entry(db, entry_id, user_id)

        self.repository.delete(db, entry)

        return {"message": "Expense entry deleted successfully"}
