from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.repositories.expense_book_repository import ExpenseBookRepository
from app.repositories.expense_entry_repository import ExpenseEntryRepository
from app.schemas.expense_book_schema import (
    ExpenseBookCreate,
    ExpenseBookUpdate
)


class ExpenseBookService:

    def __init__(self):
        self.repository = ExpenseBookRepository()
        self.entry_repository = ExpenseEntryRepository()

    # Get all of the user's books
    def get_all_books(self, db: Session, user_id: int):
        return self.repository.get_all(db, user_id)

    # Get one of the user's books (404 if missing or owned by someone else)
    def get_book(self, db: Session, book_id: int, user_id: int):
        book = self.repository.get_by_id(db, book_id, user_id)

        if not book:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Expense book not found"
            )

        return book

    # Shared name validation for create / update (names are unique per user)
    def _validate_name(
        self,
        db: Session,
        name: str,
        user_id: int,
        exclude_id: int | None = None
    ) -> str:
        book_name = name.strip()

        if not book_name:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="Book name cannot be empty"
            )

        existing = self.repository.get_by_name(db, book_name, user_id)

        if existing and existing.id != exclude_id:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Expense book already exists"
            )

        return book_name

    # Create book (new books are placed at the top of the list)
    def create_book(
        self,
        db: Session,
        book_data: ExpenseBookCreate,
        user_id: int
    ):
        book_data.name = self._validate_name(db, book_data.name, user_id)

        min_order = self.repository.get_min_display_order(db, user_id)
        display_order = (min_order - 1) if min_order is not None else 0

        return self.repository.create(db, book_data, user_id, display_order)

    # Update book
    def update_book(
        self,
        db: Session,
        book_id: int,
        book_data: ExpenseBookUpdate,
        user_id: int
    ):
        book = self.get_book(db, book_id, user_id)

        book_data.name = self._validate_name(
            db, book_data.name, user_id, exclude_id=book_id
        )

        return self.repository.update(db, book, book_data)

    # Reorder books (drag and drop)
    def reorder_books(self, db: Session, book_ids: list[int], user_id: int):
        if len(set(book_ids)) != len(book_ids):
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="Duplicate book IDs in reorder list"
            )

        existing_ids = {book.id for book in self.repository.get_all(db, user_id)}
        missing = set(book_ids) - existing_ids

        if missing:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Expense book(s) not found: {sorted(missing)}"
            )

        self.repository.reorder(db, book_ids, user_id)

        return self.repository.get_all(db, user_id)

    # Delete book
    def delete_book(self, db: Session, book_id: int, user_id: int):
        book = self.get_book(db, book_id, user_id)

        # Entries table has no FK cascade, so remove the book's entries
        # first; the book delete below commits both together
        self.entry_repository.delete_by_book(db, book_id)
        self.repository.delete(db, book)

        return {"message": "Expense book deleted successfully"}
