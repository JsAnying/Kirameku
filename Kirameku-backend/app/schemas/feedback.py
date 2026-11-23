from datetime import datetime
from typing import Literal
from pydantic import BaseModel, ConfigDict, Field

FeedbackType = Literal["bug", "suggestion", "other"]
FeedbackStatus = Literal["pending", "processing", "resolved", "ignored"]


class FeedbackCreate(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid")
    type: FeedbackType = "bug"
    content: str = Field(min_length=5, max_length=2000)
    contact: str = Field(default="", max_length=200)


class FeedbackUpdate(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid")
    status: FeedbackStatus
    admin_note: str = Field(default="", max_length=2000)


class FeedbackOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    type: FeedbackType
    content: str
    contact: str
    status: FeedbackStatus
    admin_note: str
    created_at: datetime
    updated_at: datetime


class FeedbackList(BaseModel):
    items: list[FeedbackOut]
    total: int
