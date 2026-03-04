from fastapi import APIRouter, Query
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from app.api.dependencies import SessionDep
from app.models.folder import Folder
from app.models.file import File
from app.schemas.search import SearchResponse

router = APIRouter(prefix="/search", tags=["search"])

@router.get("", response_model=SearchResponse)
async def global_search(session: SessionDep, query: str = Query(..., min_length=1, description="Search term for files and folders"),):
    search_term = f"%{query}%"
    folders_query = select(Folder).where(Folder.name.ilike(search_term))
    folders_result = await session.execute(folders_query)
    folders = folders_result.scalars().all()
    files_query = select(File).where(File.name.ilike(search_term), File.is_deleted == False)
    files_result = await session.execute(files_query)
    files = files_result.scalars().all()
    return SearchResponse(
        folders=folders,
        files=files,
    )

@router.get("/favorites", response_model=SearchResponse)
async def get_favorites(session: SessionDep):
    folders_query = (
        select(Folder)
        .options(selectinload(Folder.files))
        .where(Folder.is_favorite == True)
    )
    folders_result = await session.execute(folders_query)
    folders = folders_result.scalars().all()
    for f in folders:
        f.files_count = len([file for file in f.files if not file.is_deleted])
    files_query = select(File).where(File.is_favorite == True, File.is_deleted == False)
    files_result = await session.execute(files_query)
    files = files_result.scalars().all()
    return SearchResponse(
        folders=folders,
        files=files,
    )

@router.get("/trash", response_model=SearchResponse)
async def get_trash(session: SessionDep):
    files_query = select(File).where(File.is_deleted == True)
    files_result = await session.execute(files_query)
    files = files_result.scalars().all()
    return SearchResponse(
        folders=[],
        files=files,
    )