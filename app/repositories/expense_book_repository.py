from sqlalchemy import func
from sqlalchemy.orm import Session

from app.models import ExpenseBook
from app.schemas.expense_book_schema import (
    ExpenseBookCreate,
    ExpenseBookUpdate
)


class ExpenseBookRepository:
    """Every query is limited to one user's books."""

    # Get all of a user's books (newest first when order is equal)
    def get_all(self, db: Session, user_id: int):
        return (
            db.query(ExpenseBook)
            .filter(ExpenseBook.user_id == user_id)
            .order_by(ExpenseBook.display_order.asc(), ExpenseBook.id.desc())
            .all()
        )

    # Get a user's book by ID (None if it belongs to someone else)
    def get_by_id(self, db: Session, book_id: int, user_id: int):
        return (
            db.query(ExpenseBook)
            .filter(ExpenseBook.id == book_id, ExpenseBook.user_id == user_id)
            .first()
        )

    # Find one of the user's books by name (case-insensitive)
    def get_by_name(self, db: Session, name: str, user_id: int):
        return (
            db.query(ExpenseBook)
            .filter(
                ExpenseBook.user_id == user_id,
                func.lower(ExpenseBook.name) == name.lower()
            )
            .first()
        )

    # Smallest display_order among the user's books (used to put new books on top)
    def get_min_display_order(self, db: Session, user_id: int) -> int | None:
        return (
            db.query(func.min(ExpenseBook.display_order))
            .filter(ExpenseBook.user_id == user_id)
            .scalar()
        )

    # Create expense book
    def create(
        self,
        db: Session,
        book_data: ExpenseBookCreate,
        user_id: int,
        display_order: int = 0
    ):
        new_book = ExpenseBook(
            name=book_data.name.strip(),
            description=book_data.description,
            display_order=display_order,
            user_id=user_id
        )

        db.add(new_book)
        db.commit()
        db.refresh(new_book)

        return new_book

    # Update expense book
    def update(
        self,
        db: Session,
        book: ExpenseBook,
        book_data: ExpenseBookUpdate
    ):
        book.name = book_data.name.strip()
        book.description = book_data.description

        if book_data.display_order is not None:
            book.display_order = book_data.display_order

        db.commit()
        db.refresh(book)

        return book

    # Save a new order: position in the list becomes display_order
    def reorder(self, db: Session, book_ids: list[int], user_id: int):
        books = (
            db.query(ExpenseBook)
            .filter(ExpenseBook.id.in_(book_ids), ExpenseBook.user_id == user_id)
            .all()
        )
        books_by_id = {book.id: book for book in books}

        for position, book_id in enumerate(book_ids):
            books_by_id[book_id].display_order = position

        db.commit()

    # Delete expense book
    def delete(self, db: Session, book: ExpenseBook):
        db.delete(book)
        db.commit()
