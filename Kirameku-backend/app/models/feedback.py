from datetime import datetime
from sqlmodel import SQLModel, Field


class Feedback(SQLModel, table=True):
    __tablename__ = "feedback"

    id: int | None = Field(default=None, primary_key=True)
    type: str = Field(max_length=20, index=True)
    content: str = Field(max_length=2000)
    contact: str = Field(default="", max_length=200)
    status: str = Field(default="pending", max_length=20, index=True)
    admin_note: str = Field(default="", max_length=2000)
    created_at: datetime = Field(default_factory=datetime.now, index=True)
    updated_at: datetime = Field(default_factory=datetime.now)
