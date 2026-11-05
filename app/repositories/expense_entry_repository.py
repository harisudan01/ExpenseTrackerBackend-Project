from datetime import date

from sqlalchemy import func, or_, case
from sqlalchemy.orm import Session

from app.models import ExpenseEntry
from app.schemas.expense_entry_schema import (
    ExpenseEntryCreate,
    ExpenseEntryUpdate
)


class ExpenseEntryRepository:

    # Get entries of a book (newest first) with optional filters
    def get_by_book(
        self,
        db: Session,
        book_id: int,
        transaction_type: str | None = None,
        start_date: date | None = None,
        end_date: date | None = None,
        search: str | None = None
    ):
        query = db.query(ExpenseEntry).filter(ExpenseEntry.book_id == book_id)

        if transaction_type:
            query = query.filter(ExpenseEntry.transaction_type == transaction_type)
        if start_date:
            query = query.filter(ExpenseEntry.transaction_date >= start_date)
        if end_date:
            query = query.filter(ExpenseEntry.transaction_date <= end_date)
        if search:
            pattern = f"%{search.strip()}%"
            query = query.filter(
                or_(
                    ExpenseEntry.remarks.ilike(pattern),
                    ExpenseEntry.party.ilike(pattern),
                    ExpenseEntry.category.ilike(pattern)
                )
            )

        return query.order_by(
            ExpenseEntry.transaction_date.desc(),
            ExpenseEntry.transaction_time.desc().nulls_last(),
            ExpenseEntry.id.desc()
        ).all()

    # Get entry by ID
    def get_by_id(self, db: Session, entry_id: int):
        return (
            db.query(ExpenseEntry)
            .filter(ExpenseEntry.id == entry_id)
            .first()
        )

    # Cash in / cash out totals for a book, calculated in the database
    def get_summary(self, db: Session, book_id: int):
        cash_in = func.coalesce(func.sum(
            case((ExpenseEntry.transaction_type == "Cash In", ExpenseEntry.amount), else_=0)
        ), 0)
        cash_out = func.coalesce(func.sum(
            case((ExpenseEntry.transaction_type == "Cash Out", ExpenseEntry.amount), else_=0)
        ), 0)

        return (
            db.query(func.count(ExpenseEntry.id), cash_in, cash_out)
            .filter(ExpenseEntry.book_id == book_id)
            .one()
        )

    # Create entry
    def create(self, db: Session, book_id: int, entry_data: ExpenseEntryCreate):
        new_entry = ExpenseEntry(book_id=book_id, **entry_data.model_dump())

        db.add(new_entry)
        db.commit()
        db.refresh(new_entry)

        return new_entry

    # Update entry
    def update(
        self,
        db: Session,
        entry: ExpenseEntry,
        entry_data: ExpenseEntryUpdate
    ):
        for field, value in entry_data.model_dump().items():
            setattr(entry, field, value)

        db.commit()
        db.refresh(entry)

        return entry

    # Delete entry
    def delete(self, db: Session, entry: ExpenseEntry):
        db.delete(entry)
        db.commit()

    # Delete all entries of a book (no commit, so it runs in the
    # same transaction as the book delete)
    def delete_by_book(self, db: Session, book_id: int):
        (
            db.query(ExpenseEntry)
            .filter(ExpenseEntry.book_id == book_id)
            .delete(synchronize_session=False)
        )
