from datetime import datetime
from typing import Optional
from pydantic import BaseModel, ConfigDict


class FileRename(BaseModel):
    name: str


class FileFavoriteToggle(BaseModel):
    is_favorite: bool


class FileResponse(BaseModel):
    id: int
    name: str
    size: Optional[int]
    folder_id: Optional[int]
    is_deleted: bool
    is_favorite: bool
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)