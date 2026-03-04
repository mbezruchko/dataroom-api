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
    # Resolve Workspace
    from app.models.workspace import Workspace
    if folder_in.workspace_guid:
        res = await session.execute(select(Workspace).where(Workspace.guid == folder_in.workspace_guid))
        workspace = res.scalar_one_or_none()
        if not workspace:
            raise HTTPException(status_code=404, detail="Workspace not found")
        workspace_id = workspace.id
    else:
        # Default to first workspace for now if not provided
        res = await session.execute(select(Workspace).limit(1))
        workspace = res.scalar_one_or_none()
        if not workspace:
            # Create a default one if none exists (fallback)
            workspace = Workspace(name="Default Workspace")
            session.add(workspace)
            await session.flush()
        workspace_id = workspace.id

    parent_id = None
    if folder_in.parent_guid:
        result = await session.execute(
            select(Folder).where(Folder.guid == folder_in.parent_guid)
        )
        parent_folder = result.scalar_one_or_none()
        if not parent_folder:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Parent folder not found",
            )
        parent_id = parent_folder.id

    new_folder = Folder(
        name=folder_in.name,
        parent_id=parent_id,
        workspace_id=workspace_id
    )
    session.add(new_folder)
    await session.commit()
    await session.refresh(new_folder)
    return new_folder

@router.get("", response_model=List[FolderResponseMinimal])
async def list_root_folders(session: SessionDep, workspace_guid: Optional[str] = None):
    # Ensure nested files for count are also filtered
    query = (
        select(Folder)
        .options(selectinload(Folder.files.and_(File.is_deleted == False)))
        .where(Folder.parent_id == None)
    )
    
    if workspace_guid:
        from app.models.workspace import Workspace
        res = await session.execute(select(Workspace).where(Workspace.guid == workspace_guid))
        workspace = res.scalar_one_or_none()
        if workspace:
            query = query.where(Folder.workspace_id == workspace.id)

    result = await session.execute(query)
    folders = result.scalars().all()
    for f in folders:
        f.files_count = len(f.files)
    return folders

@router.get("/{guid}", response_model=FolderResponseDetailed)
async def get_folder(guid: str, session: SessionDep):
    query = (
        select(Folder)
        .options(
            selectinload(Folder.subfolders).selectinload(Folder.files.and_(File.is_deleted == False)),
            selectinload(Folder.files.and_(File.is_deleted == False)),
        )
        .where(Folder.guid == guid)
    )
    result = await session.execute(query)
    folder = result.scalar_one_or_none()
    if not folder:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Folder not found",
        )

    for sub in folder.subfolders:
        sub.files_count = len(sub.files)

    return folder

@router.get("/{guid}/path", response_model=List[FolderBreadcrumb])
async def get_folder_path(guid: str, session: SessionDep):
    result = await session.execute(select(Folder).where(Folder.guid == guid))
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

@router.patch("/{guid}", response_model=FolderResponseMinimal)
async def rename_folder(guid: str, folder_in: FolderRename, session: SessionDep):
    result = await session.execute(select(Folder).where(Folder.guid == guid))
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

@router.patch("/{guid}/favorite", response_model=FolderResponseMinimal)
async def toggle_favorite(guid: str, favorite_in: FolderFavoriteToggle, session: SessionDep):
    result = await session.execute(select(Folder).where(Folder.guid == guid))
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

@router.delete("/{guid}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_folder(guid: str, session: SessionDep):
    result = await session.execute(select(Folder).where(Folder.guid == guid))
    folder = result.scalar_one_or_none()

    if not folder:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Folder not found",
        )

    async def process_folder_files(current_id: int):
        # We mark files as deleted and move them to "no folder" (root trash)
        await session.execute(
            update(File)
            .where(File.folder_id == current_id)
            .values(is_deleted=True, folder_id=None)
        )
        res = await session.execute(select(Folder).where(Folder.parent_id == current_id))
        children = res.scalars().all()
        for child in children:
            await process_folder_files(child.id)
            
    await process_folder_files(folder.id)
    # Folders are still hard-deleted as requested (they don't have is_deleted)
    await session.delete(folder)
    await session.commit()
    return