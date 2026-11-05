from datetime import datetime

from pydantic import BaseModel, Field, ConfigDict


# Data required when creating an expense book
class ExpenseBookCreate(BaseModel):
    name: str = Field(
        min_length=1,
        max_length=150
    )
    description: str | None = None


# Data allowed when updating an expense book
class ExpenseBookUpdate(BaseModel):
    name: str = Field(
        min_length=1,
        max_length=150
    )
    description: str | None = None
    # None = keep the current position, so a rename does not reset the order
    display_order: int | None = None


# Ordered list of book IDs after a drag and drop
class ExpenseBookReorder(BaseModel):
    book_ids: list[int] = Field(min_length=1)


# Data returned by the API
class ExpenseBookResponse(BaseModel):
    id: int
    name: str
    description: str | None
    display_order: int
    created_at: datetime | None = None
    updated_at: datetime | None = None

    model_config = ConfigDict(from_attributes=True)
