from typing import List, Optional
from fastapi import APIRouter, HTTPException, status
from sqlalchemy import select, update
from sqlalchemy.orm import selectinload
from app.api.dependencies import SessionDep
from app.models.folder import Folder
from app.models.file import File
from app.schemas.folder import (
    FolderCreate,
    FolderRename,
    FolderFavoriteToggle,
    FolderResponseMinimal,
    FolderResponseDetailed,
    FolderBreadcrumb,
)

router = APIRouter(prefix="/folders", tags=["folders"])

@router.post("", response_model=FolderResponseMinimal, status_code=status.HTTP_201_CREATED)
async def create_folder(folder_in: FolderCreate, session: SessionDep):
    if folder_in.parent_id is not None:
        result = await session.execute(
            select(Folder).where(Folder.id == folder_in.parent_id)
        )
        parent_folder = result.scalar_one_or_none()
        if not parent_folder:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Parent folder not found",
            )
    new_folder = Folder(
        name=folder_in.name,
        parent_id=folder_in.parent_id,
    )
    session.add(new_folder)
    await session.commit()
    await session.refresh(new_folder)
    return new_folder

@router.get("", response_model=List[FolderResponseMinimal])
async def list_root_folders(session: SessionDep):
    result = await session.execute(
        select(Folder)
        .options(selectinload(Folder.files))
        .where(Folder.parent_id == None)
    )
    folders = result.scalars().all()
    for f in folders:
        f.files_count = len([file for file in f.files if not file.is_deleted])
    return folders

@router.get("/{folder_id}", response_model=FolderResponseDetailed)
async def get_folder(folder_id: int, session: SessionDep):
    query = (
        select(Folder)
        .options(
            selectinload(Folder.subfolders).selectinload(Folder.files),
            selectinload(Folder.files.and_(File.is_deleted == False)),
        )
        .where(Folder.id == folder_id)
    )
    result = await session.execute(query)
    folder = result.scalar_one_or_none()
    if not folder:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Folder not found",
        )

    for sub in folder.subfolders:
        sub.files_count = len([file for file in sub.files if not file.is_deleted])

    return folder

@router.get("/{folder_id}/path", response_model=List[FolderBreadcrumb])
async def get_folder_path(folder_id: int, session: SessionDep):
    result = await session.execute(select(Folder).where(Folder.id == folder_id))
    current_folder = result.scalar_one_or_none()

    if not current_folder:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Folder not found",
        )
    path = []
    while current_folder is not None:
        path.append(current_folder)
        if current_folder.parent_id is None:
            break
        result = await session.execute(
            select(Folder).where(Folder.id == current_folder.parent_id)
        )
        current_folder = result.scalar_one_or_none()
    path.reverse()
    return path

@router.patch("/{folder_id}", response_model=FolderResponseMinimal)
async def rename_folder(folder_id: int, folder_in: FolderRename, session: SessionDep):
    result = await session.execute(select(Folder).where(Folder.id == folder_id))
    folder = result.scalar_one_or_none()
    if not folder:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Folder not found",
        )
    folder.name = folder_in.name
    await session.commit()
    await session.refresh(folder)
    return folder

@router.patch("/{folder_id}/favorite", response_model=FolderResponseMinimal)
async def toggle_favorite(folder_id: int, favorite_in: FolderFavoriteToggle, session: SessionDep):
    result = await session.execute(select(Folder).where(Folder.id == folder_id))
    folder = result.scalar_one_or_none()
    if not folder:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Folder not found",
        )
    folder.is_favorite = favorite_in.is_favorite
    await session.commit()
    await session.refresh(folder)
    return folder

async def _soft_delete_recursively(folder_id: int, session: SessionDep):
    await session.execute(
        update(File)
        .where(File.folder_id == folder_id, File.is_deleted == False)
        .values(is_deleted=True)
    )
    result = await session.execute(
        select(Folder).where(Folder.parent_id == folder_id)
    )
    subfolders = result.scalars().all()
    for subfolder in subfolders:
        await _soft_delete_recursively(subfolder.id, session)
    pass

@router.delete("/{folder_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_folder(folder_id: int, session: SessionDep):
    result = await session.execute(select(Folder).where(Folder.id == folder_id))
    folder = result.scalar_one_or_none()

    if not folder:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Folder not found",
        )

    async def process_folder(current_id: int):
        await session.execute(
            update(File)
            .where(File.folder_id == current_id)
            .values(is_deleted=True, folder_id=None)
        )
        res = await session.execute(select(Folder).where(Folder.parent_id == current_id))
        children = res.scalars().all()
        for child in children:
            await process_folder(child.id)
    await process_folder(folder_id)
    await session.delete(folder)
    await session.commit()
    return