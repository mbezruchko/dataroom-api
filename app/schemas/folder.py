from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, ConfigDict


class FileResponseMinimal(BaseModel):
    id: int
    guid: str
    name: str
    size: Optional[int]
    is_deleted: bool
    is_favorite: bool
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class FolderBase(BaseModel):
    name: str


class FolderCreate(FolderBase):
    workspace_guid: Optional[str] = None
    parent_guid: Optional[str] = None


class FolderRename(FolderBase):
    pass


class FolderFavoriteToggle(BaseModel):
    is_favorite: bool


class FolderBreadcrumb(BaseModel):
    id: int
    guid: str
    name: str

    model_config = ConfigDict(from_attributes=True)


class FolderResponseMinimal(FolderBase):
    id: int
    guid: str
    workspace_id: int
    parent_id: Optional[int]
    is_favorite: bool
    files_count: int = 0
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class FolderResponseDetailed(FolderResponseMinimal):
    subfolders: List[FolderResponseMinimal] = []
    files: List[FileResponseMinimal] = []