import os
import uuid
import shutil
from typing import List, Optional
from fastapi import APIRouter, UploadFile, File as FastAPIFile, HTTPException, status, Form
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from app.api.dependencies import SessionDep
from app.models.file import File
from app.models.folder import Folder
from app.schemas.file import FileResponse, FileUpdate, FileFavoriteToggle
from app.core.config import settings

router = APIRouter(prefix="/files", tags=["files"])

@router.get("", response_model=List[FileResponse])
async def list_files(
    session: SessionDep, 
    folder_id: Optional[int] = None, 
    workspace_guid: Optional[str] = None
):
    query = select(File).where(File.is_deleted == False)
    
    if workspace_guid:
        from app.models.workspace import Workspace
        res = await session.execute(select(Workspace).where(Workspace.guid == workspace_guid))
        workspace = res.scalar_one_or_none()
        if workspace:
            query = query.where(File.workspace_id == workspace.id)

    if folder_id is None:
        query = query.where(File.folder_id == None)
    else:
        query = query.where(File.folder_id == folder_id)
    result = await session.execute(query)
    return result.scalars().all()


@router.post("/upload", response_model=List[FileResponse], status_code=status.HTTP_201_CREATED)
async def upload_files(
    session: SessionDep,
    files: List[UploadFile] = FastAPIFile(...),
    folder_guid: Optional[str] = Form(None),
    workspace_guid: Optional[str] = Form(None),
):
    from app.models.workspace import Workspace
    
    # Resolve Workspace
    if workspace_guid:
        res = await session.execute(select(Workspace).where(Workspace.guid == workspace_guid))
        workspace = res.scalar_one_or_none()
        if not workspace:
            raise HTTPException(status_code=404, detail="Workspace not found")
        workspace_id = workspace.id
    else:
        # Fallback to default
        res = await session.execute(select(Workspace).limit(1))
        workspace = res.scalar_one_or_none()
        if not workspace:
            workspace = Workspace(name="Default Workspace")
            session.add(workspace)
            await session.flush()
        workspace_id = workspace.id

    # Resolve Folder
    folder_id = None
    if folder_guid:
        res = await session.execute(select(Folder).where(Folder.guid == folder_guid))
        folder = res.scalar_one_or_none()
        if not folder:
            raise HTTPException(status_code=404, detail="Folder not found")
        folder_id = folder.id

    uploaded_files = []
    
    # Ensure storage path exists
    os.makedirs(settings.STORAGE_PATH, exist_ok=True)

    for file in files:
        file_guid = str(uuid.uuid4())
        file_extension = os.path.splitext(file.filename)[1]
        storage_filename = f"{file_guid}{file_extension}"
        storage_path = os.path.join(settings.STORAGE_PATH, storage_filename)

        with open(storage_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)

        new_file = File(
            guid=file_guid,
            name=file.filename,
            size=os.path.getsize(storage_path),
            storage_path=storage_path,
            folder_id=folder_id,
            workspace_id=workspace_id
        )
        session.add(new_file)
        uploaded_files.append(new_file)

    await session.commit()
    for f in uploaded_files:
        await session.refresh(f)
        
    return uploaded_files

@router.get("/{guid}/download")
async def download_file(guid: str, session: SessionDep):
    result = await session.execute(select(File).where(File.guid == guid))
    file = result.scalar_one_or_none()
    
    if not file or not os.path.exists(file.storage_path):
        raise HTTPException(status_code=404, detail="File not found")

    from fastapi.responses import FileResponse as FastAPIFileResponse
    
    return FastAPIFileResponse(
        path=file.storage_path,
        filename=file.name,
        media_type="application/pdf"
    )

@router.patch("/{guid}", response_model=FileResponse)
async def update_file(guid: str, file_in: FileUpdate, session: SessionDep):
    result = await session.execute(select(File).where(File.guid == guid))
    file = result.scalar_one_or_none()
    if not file:
        raise HTTPException(status_code=404, detail="File not found")
    
    if file_in.name is not None:
        file.name = file_in.name
    await session.commit()
    await session.refresh(file)
    return file

@router.patch("/{guid}/favorite", response_model=FileResponse)
async def toggle_favorite(guid: str, favorite_in: FileFavoriteToggle, session: SessionDep):
    result = await session.execute(select(File).where(File.guid == guid))
    file = result.scalar_one_or_none()
    if not file:
        raise HTTPException(status_code=404, detail="File not found")
    file.is_favorite = favorite_in.is_favorite
    await session.commit()
    await session.refresh(file)
    return file

@router.delete("/{guid}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_file(guid: str, session: SessionDep):
    result = await session.execute(select(File).where(File.guid == guid))
    file = result.scalar_one_or_none()
    if not file:
        raise HTTPException(status_code=404, detail="File not found")
    
    file.is_deleted = True
    await session.commit()
    return

@router.post("/{guid}/restore", response_model=FileResponse)
async def restore_file(guid: str, session: SessionDep):
    result = await session.execute(select(File).where(File.guid == guid))
    file = result.scalar_one_or_none()
    if not file:
        raise HTTPException(status_code=404, detail="File not found")
    
    file.is_deleted = False
    await session.commit()
    await session.refresh(file)
    return file