from datetime import date, time, datetime
from decimal import Decimal
from typing import Literal

from pydantic import BaseModel, Field, ConfigDict, field_validator


TransactionType = Literal["Cash In", "Cash Out"]


# Fields shared by create and update
class ExpenseEntryBase(BaseModel):
    transaction_date: date
    transaction_time: time | None = None
    amount: Decimal = Field(gt=0, max_digits=12, decimal_places=2)
    category: str | None = Field(default=None, max_length=100)
    transaction_type: TransactionType
    party: str | None = Field(default=None, max_length=150)
    remarks: str | None = None

    # Trim text fields and store empty strings as NULL
    @field_validator("category", "party", "remarks", mode="before")
    @classmethod
    def blank_to_none(cls, value):
        if isinstance(value, str):
            value = value.strip()
            return value or None
        return value


# Data required when creating an entry (book_id comes from the URL)
class ExpenseEntryCreate(ExpenseEntryBase):
    pass


# Data allowed when updating an entry
class ExpenseEntryUpdate(ExpenseEntryBase):
    pass


# Data returned by the API
class ExpenseEntryResponse(BaseModel):
    id: int
    book_id: int
    transaction_date: date
    transaction_time: time | None
    amount: float
    category: str | None
    transaction_type: TransactionType
    party: str | None
    remarks: str | None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


# Totals for a book
class ExpenseEntrySummary(BaseModel):
    book_id: int
    total_entries: int
    cash_in: float
    cash_out: float
    net_balance: float
