from typing import List
from fastapi import APIRouter, status
from sqlalchemy import select
from app.api.dependencies import SessionDep
from app.models.workspace import Workspace
from app.schemas.workspace import WorkspaceResponse, WorkspaceCreate

router = APIRouter(prefix="/workspaces", tags=["workspaces"])

@router.get("", response_model=List[WorkspaceResponse])
async def list_workspaces(session: SessionDep):
    result = await session.execute(
        select(Workspace).where(Workspace.is_deleted == False)
    )
    return result.scalars().all()

@router.post("", response_model=WorkspaceResponse, status_code=status.HTTP_201_CREATED)
async def create_workspace(workspace_in: WorkspaceCreate, session: SessionDep):
    new_workspace = Workspace(
        name=workspace_in.name,
        description=workspace_in.description
    )
    session.add(new_workspace)
    await session.commit()
    await session.refresh(new_workspace)
    return new_workspace
