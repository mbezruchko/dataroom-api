from typing import List, Optional
from fastapi import APIRouter, status, Cookie, HTTPException
from sqlalchemy import select
from app.api.dependencies import SessionDep
from app.models.workspace import Workspace
from app.schemas.workspace import WorkspaceResponse, WorkspaceCreate, WorkspaceUpdate

router = APIRouter(prefix="/workspaces", tags=["workspaces"])

@router.get("", response_model=List[WorkspaceResponse])
async def list_workspaces(
    session: SessionDep, 
    session_guid: Optional[str] = Cookie(None)
):
    query = select(Workspace)
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

@router.get("/{guid}", response_model=WorkspaceResponse)
async def get_workspace(guid: str, session: SessionDep):
    result = await session.execute(select(Workspace).where(Workspace.guid == guid))
    workspace = result.scalar_one_or_none()
    if not workspace:
        raise HTTPException(status_code=404, detail="Workspace not found")
    return workspace

@router.patch("/{guid}", response_model=WorkspaceResponse)
async def update_workspace(
    guid: str, 
    workspace_in: WorkspaceUpdate, 
    session: SessionDep
):
    result = await session.execute(select(Workspace).where(Workspace.guid == guid))
    workspace = result.scalar_one_or_none()
    if not workspace:
        raise HTTPException(status_code=404, detail="Workspace not found")
    
    if workspace_in.name is not None:
        workspace.name = workspace_in.name
    if workspace_in.description is not None:
        workspace.description = workspace_in.description
    
    await session.commit()
    await session.refresh(workspace)
    return workspace

@router.delete("/{guid}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_workspace(guid: str, session: SessionDep):
    result = await session.execute(select(Workspace).where(Workspace.guid == guid))
    workspace = result.scalar_one_or_none()
    if not workspace:
        raise HTTPException(status_code=404, detail="Workspace not found")
    
    # Optionally delete physical files from disk
    from app.models.file import File
    import os
    
    file_paths_res = await session.execute(select(File.storage_path).where(File.workspace_id == workspace.id))
    file_paths = file_paths_res.scalars().all()
    
    for path in file_paths:
        try:
            if os.path.exists(path):
                os.remove(path)
        except Exception:
            pass # Best effort deletion

    await session.delete(workspace)
    await session.commit()
    return
