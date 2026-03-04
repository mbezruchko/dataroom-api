from typing import Optional
from fastapi import APIRouter, Query
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from app.api.dependencies import SessionDep
from app.models.folder import Folder
from app.models.file import File
from app.schemas.search import SearchResponse

router = APIRouter(prefix="/search", tags=["search"])

@router.get("", response_model=SearchResponse)
async def global_search(
    session: SessionDep, 
    query: str = Query(..., min_length=1, description="Search term for files and folders"),
    workspace_guid: Optional[str] = None
):
    search_term = f"%{query}%"
    # Note: Folder does not have is_deleted field
    folders_query = select(Folder).where(Folder.name.ilike(search_term))
    files_query = select(File).where(File.name.ilike(search_term), File.is_deleted == False)
    
    if workspace_guid:
        from app.models.workspace import Workspace
        res = await session.execute(select(Workspace).where(Workspace.guid == workspace_guid))
        workspace = res.scalar_one_or_none()
        if workspace:
            folders_query = folders_query.where(Folder.workspace_id == workspace.id)
            files_query = files_query.where(File.workspace_id == workspace.id)

    folders_result = await session.execute(folders_query)
    folders = folders_result.scalars().all()
    files_result = await session.execute(files_query)
    files = files_result.scalars().all()
    return SearchResponse(
        folders=folders,
        files=files,
    )

@router.get("/favorites", response_model=SearchResponse)
async def get_favorites(session: SessionDep, workspace_guid: Optional[str] = None):
    # Note: Folder does not have is_deleted field
    folders_query = (
        select(Folder)
        .options(selectinload(Folder.files.and_(File.is_deleted == False)))
        .where(Folder.is_favorite == True)
    )
    files_query = select(File).where(File.is_favorite == True, File.is_deleted == False)

    if workspace_guid:
        from app.models.workspace import Workspace
        res = await session.execute(select(Workspace).where(Workspace.guid == workspace_guid))
        workspace = res.scalar_one_or_none()
        if workspace:
            folders_query = folders_query.where(Folder.workspace_id == workspace.id)
            files_query = files_query.where(File.workspace_id == workspace.id)

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
async def get_trash(session: SessionDep, workspace_guid: Optional[str] = None):
    files_query = select(File).where(File.is_deleted == True)
    
    if workspace_guid:
        from app.models.workspace import Workspace
        res = await session.execute(select(Workspace).where(Workspace.guid == workspace_guid))
        workspace = res.scalar_one_or_none()
        if workspace:
            files_query = files_query.where(File.workspace_id == workspace.id)

    files_result = await session.execute(files_query)
    files = files_result.scalars().all()
    return SearchResponse(
        folders=[],
        files=files,
    )