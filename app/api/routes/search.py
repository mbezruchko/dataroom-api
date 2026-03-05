import os
from typing import Optional
from fastapi import APIRouter, Query, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from app.api.dependencies import SessionDep, SessionGuidDep, check_workspace_access
from app.models.folder import Folder
from app.models.file import File
from app.models.workspace import Workspace
from app.schemas.search import SearchResponse

router = APIRouter(prefix="/search", tags=["search"])

@router.get("", response_model=SearchResponse)
async def global_search(
    session: SessionDep, 
    session_guid: SessionGuidDep,
    query: str = Query(..., min_length=1, description="Search term for files and folders"),
    workspace_guid: Optional[str] = None
):
    search_term = f"%{query}%"
    
    folders_query = select(Folder).where(Folder.name.ilike(search_term))
    files_query = select(File).where(File.name.ilike(search_term), File.is_deleted == False)
    deleted_files_query = select(File).where(File.name.ilike(search_term), File.is_deleted == True)
    
    if workspace_guid:
        res = await session.execute(select(Workspace).where(Workspace.guid == workspace_guid))
        workspace = res.scalar_one_or_none()
        if not workspace:
            raise HTTPException(status_code=404, detail="Workspace not found")
        
        await check_workspace_access(workspace, session_guid)
        
        folders_query = folders_query.where(Folder.workspace_id == workspace.id)
        files_query = files_query.where(File.workspace_id == workspace.id)
        deleted_files_query = deleted_files_query.where(File.workspace_id == workspace.id)
    elif session_guid:
        folders_query = folders_query.join(Workspace).where(Workspace.session_guid == session_guid)
        files_query = files_query.join(Workspace).where(Workspace.session_guid == session_guid)
        deleted_files_query = deleted_files_query.join(Workspace).where(Workspace.session_guid == session_guid)

    folders_result = await session.execute(folders_query)
    folders = folders_result.scalars().all()
    
    files_result = await session.execute(files_query)
    files = files_result.scalars().all()
    
    deleted_files_result = await session.execute(deleted_files_query)
    deleted_files = deleted_files_result.scalars().all()

    return SearchResponse(
        folders=folders,
        files=files,
        deleted_files=deleted_files
    )

@router.get("/favorites", response_model=SearchResponse)
async def get_favorites(
    session: SessionDep, 
    session_guid: SessionGuidDep,
    workspace_guid: Optional[str] = None
):
    folders_query = (
        select(Folder)
        .options(selectinload(Folder.files.and_(File.is_deleted == False)))
        .where(Folder.is_favorite == True)
    )
    files_query = select(File).where(File.is_favorite == True, File.is_deleted == False)

    if workspace_guid:
        res = await session.execute(select(Workspace).where(Workspace.guid == workspace_guid))
        workspace = res.scalar_one_or_none()
        if not workspace:
            raise HTTPException(status_code=404, detail="Workspace not found")
        
        await check_workspace_access(workspace, session_guid)
        folders_query = folders_query.where(Folder.workspace_id == workspace.id)
        files_query = files_query.where(File.workspace_id == workspace.id)
    elif session_guid:
        folders_query = folders_query.join(Workspace).where(Workspace.session_guid == session_guid)
        files_query = files_query.join(Workspace).where(Workspace.session_guid == session_guid)

    folders_result = await session.execute(folders_query)
    folders = folders_result.scalars().all()
    for f in folders:
        f.files_count = len(f.files)
    
    files_result = await session.execute(files_query)
    files = files_result.scalars().all()
    return SearchResponse(
        folders=folders,
        files=files,
    )

@router.get("/trash", response_model=SearchResponse)
async def get_trash(
    session: SessionDep, 
    session_guid: SessionGuidDep,
    workspace_guid: Optional[str] = None
):
    files_query = select(File).where(File.is_deleted == True)
    
    if workspace_guid:
        res = await session.execute(select(Workspace).where(Workspace.guid == workspace_guid))
        workspace = res.scalar_one_or_none()
        if not workspace:
            raise HTTPException(status_code=404, detail="Workspace not found")
            
        await check_workspace_access(workspace, session_guid)
        files_query = files_query.where(File.workspace_id == workspace.id)
    elif session_guid:
        files_query = files_query.join(Workspace).where(Workspace.session_guid == session_guid)

    files_result = await session.execute(files_query)
    files = files_result.scalars().all()
    return SearchResponse(
        folders=[],
        files=files,
    )

@router.delete("/trash/empty", status_code=204)
async def empty_trash(
    session: SessionDep, 
    session_guid: SessionGuidDep,
    workspace_guid: str
):
    # Find workspace
    res = await session.execute(select(Workspace).where(Workspace.guid == workspace_guid))
    workspace = res.scalar_one_or_none()
    if not workspace:
        raise HTTPException(status_code=404, detail="Workspace not found")
        
    await check_workspace_access(workspace, session_guid)
    
    # Find all deleted files
    files_res = await session.execute(
        select(File).where(File.workspace_id == workspace.id, File.is_deleted == True)
    )
    files_to_delete = files_res.scalars().all()
    
    if not files_to_delete:
        return

    # Delete physical files and records
    for file in files_to_delete:
        storage_path = file.storage_path
        await session.delete(file)
        
        # Best effort physical deletion
        if storage_path and os.path.exists(storage_path):
            try:
                os.remove(storage_path)
            except OSError as e:
                print(f"Error deleting physical file {storage_path}: {e}")

    await session.commit()
    return