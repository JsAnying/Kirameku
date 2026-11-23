from datetime import datetime
from pydantic import BaseModel

from app.utils.media import ImageUrl


class AlbumCreate(BaseModel):
    title: str
    description: str = ""
    cover: ImageUrl = ""
    sort: int = 0


class AlbumUpdate(BaseModel):
    title: str | None = None
    description: str | None = None
    cover: ImageUrl | None = None
    sort: int | None = None


class AlbumOut(BaseModel):
    id: int
    title: str
    description: str
    cover: ImageUrl
    photo_count: int
    sort: int
    created_at: datetime
    updated_at: datetime


class PhotoCreate(BaseModel):
    album_id: int
    url: ImageUrl
    caption: str = ""
    orientation: str = "landscape"
    sort: int = 0


class PhotoOut(BaseModel):
    id: int
    album_id: int
    url: ImageUrl
    caption: str
    orientation: str
    sort: int
    created_at: datetime
