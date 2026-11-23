from datetime import datetime
from pydantic import BaseModel

from app.utils.media import ImageUrl


# ---- Category ----

class BookmarkCategoryCreate(BaseModel):
    name: str
    icon: ImageUrl = ""
    description: str = ""
    sort: int = 0


class BookmarkCategoryUpdate(BaseModel):
    name: str | None = None
    icon: ImageUrl | None = None
    description: str | None = None
    sort: int | None = None


class BookmarkCategoryOut(BaseModel):
    id: int
    name: str
    icon: ImageUrl
    description: str
    sort: int
    created_at: datetime
    updated_at: datetime | None = None


# ---- Site ----

class BookmarkSiteCreate(BaseModel):
    category_id: int
    name: str
    url: str
    icon: ImageUrl = ""
    description: str = ""
    platforms: list[str] = []
    sort: int = 0


class BookmarkSiteUpdate(BaseModel):
    category_id: int | None = None
    name: str | None = None
    url: str | None = None
    icon: ImageUrl | None = None
    description: str | None = None
    platforms: list[str] | None = None
    sort: int | None = None


class BookmarkSiteOut(BaseModel):
    id: int
    category_id: int
    name: str
    url: str
    icon: ImageUrl
    description: str
    platforms: list[str]
    sort: int
    created_at: datetime
    updated_at: datetime | None = None


class BookmarkFull(BookmarkCategoryOut):
    sites: list[BookmarkSiteOut] = []
