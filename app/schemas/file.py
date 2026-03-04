from datetime import datetime
from typing import Optional
from pydantic import BaseModel, ConfigDict


class FileUpdate(BaseModel):
    name: Optional[str] = None


class FileFavoriteToggle(BaseModel):
    is_favorite: bool


class FileResponse(BaseModel):
    id: int
    guid: str
    name: str
    size: Optional[int]
    folder_id: Optional[int]
    workspace_id: int
    is_deleted: bool
    is_favorite: bool
    content_hash: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)