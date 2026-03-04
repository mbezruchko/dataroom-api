from typing import List
from pydantic import BaseModel, ConfigDict
from app.schemas.folder import FolderResponseMinimal
from app.schemas.file import FileResponse


class SearchResponse(BaseModel):
    folders: List[FolderResponseMinimal]
    files: List[FileResponse]

    model_config = ConfigDict(from_attributes=True)