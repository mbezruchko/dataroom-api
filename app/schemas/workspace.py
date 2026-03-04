from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, ConfigDict

class WorkspaceBase(BaseModel):
    name: str
    description: Optional[str] = None

class WorkspaceCreate(WorkspaceBase):
    pass

class WorkspaceUpdate(WorkspaceBase):
    name: Optional[str] = None

class WorkspaceResponse(WorkspaceBase):
    id: int
    guid: str
    is_deleted: bool
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)
