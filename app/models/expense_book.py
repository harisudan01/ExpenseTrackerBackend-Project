from sqlalchemy import BigInteger, String, Text, Integer, DateTime, func
from sqlalchemy.orm import Mapped, mapped_column
from app.database.connection import Base

class ExpenseBook(Base):
    __tablename__ = "cashexpense_books"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    # Owner of the book (cashexpense_users.id). Old books start as NULL and are
    # claimed by the first account that signs up.
    user_id: Mapped[int | None] = mapped_column(BigInteger, nullable=True, index=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=True)
    created_at: Mapped[DateTime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[DateTime] = mapped_column(
    DateTime(timezone=True),
    server_default=func.now(),
    default=func.now(),
    onupdate=func.now(),
    nullable=False
)
    display_order: Mapped[int] = mapped_column(
        Integer, default=0, nullable=False
    )