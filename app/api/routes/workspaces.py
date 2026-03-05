from typing import List, Optional
from fastapi import APIRouter, status, Cookie
from sqlalchemy import select
from app.api.dependencies import SessionDep
from app.models.workspace import Workspace
from app.schemas.workspace import WorkspaceResponse, WorkspaceCreate

router = APIRouter(prefix="/workspaces", tags=["workspaces"])

@router.get("", response_model=List[WorkspaceResponse])
async def list_workspaces(
    session: SessionDep, 
    session_guid: Optional[str] = Cookie(None)
):
    query = select(Workspace).where(Workspace.is_deleted == False)
    if session_guid:
        query = query.where(Workspace.session_guid == session_guid)
    
    result = await session.execute(query)
    workspaces = result.scalars().all()

    if not workspaces and session_guid:
        default_workspace = Workspace(
            name="Default Workspace",
            session_guid=session_guid
        )
        session.add(default_workspace)
        await session.commit()
        await session.refresh(default_workspace)
        return [default_workspace]
        
    return workspaces

@router.post("", response_model=WorkspaceResponse, status_code=status.HTTP_201_CREATED)
async def create_workspace(
    workspace_in: WorkspaceCreate, 
    session: SessionDep,
    session_guid: Optional[str] = Cookie(None)
):
    final_session_guid = workspace_in.session_guid or session_guid
    
    new_workspace = Workspace(
        name=workspace_in.name,
        description=workspace_in.description,
        session_guid=final_session_guid
    )
    session.add(new_workspace)
    await session.commit()
    await session.refresh(new_workspace)
    return new_workspace
