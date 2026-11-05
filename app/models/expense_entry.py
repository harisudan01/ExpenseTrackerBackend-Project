from datetime import date, time, datetime
from decimal import Decimal

from sqlalchemy import (
    BigInteger, String, Text, Date, Time, DateTime, Numeric,
    CheckConstraint, func
)
from sqlalchemy.orm import Mapped, mapped_column

from app.database.connection import Base


class ExpenseEntry(Base):
    __tablename__ = "cashexpense_entries"
    __table_args__ = (
        CheckConstraint("amount > 0", name="chk_transaction_amount"),
        CheckConstraint(
            "transaction_type IN ('Cash In', 'Cash Out')",
            name="chk_transaction_type"
        ),
    )

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    book_id: Mapped[int] = mapped_column(BigInteger, nullable=False, index=True)
    transaction_date: Mapped[date] = mapped_column(Date, nullable=False, index=True)
    transaction_time: Mapped[time | None] = mapped_column(Time, nullable=True)
    amount: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    category: Mapped[str | None] = mapped_column(String(100), nullable=True)
    transaction_type: Mapped[str] = mapped_column(String(20), nullable=False)
    party: Mapped[str | None] = mapped_column(String(150), nullable=True)
    remarks: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False
    )
