from datetime import datetime
from pydantic import BaseModel

from app.utils.media import ImageUrl


class FriendLinkCreate(BaseModel):
    name: str
    url: str
    avatar: ImageUrl = ""
    description: str = ""
    sort: int = 0


class FriendLinkUpdate(BaseModel):
    name: str | None = None
    url: str | None = None
    avatar: ImageUrl | None = None
    description: str | None = None
    sort: int | None = None
    is_approved: bool | None = None


class FriendLinkOut(BaseModel):
    id: int
    name: str
    url: str
    avatar: ImageUrl
    description: str
    sort: int
    is_approved: bool
    created_at: datetime
    updated_at: datetime | None = None
