import os
import uuid
import aiofiles
import hashlib
from typing import Optional

from fastapi import APIRouter, HTTPException, status, UploadFile, File as FastAPIFile, Form
from fastapi.responses import FileResponse as FastAPIFileResponse
from sqlalchemy import select

from app.api.dependencies import SessionDep
from app.core.config import settings
from app.models.folder import Folder
from app.models.file import File
from app.schemas.file import FileResponse, FileRename, FileFavoriteToggle
from typing import List

router = APIRouter(prefix="/files", tags=["files"])




@router.get("", response_model=List[FileResponse])
async def list_files(session: SessionDep, folder_id: Optional[int] = None):
    query = select(File).where(File.is_deleted == False)
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
):
    from app.models.workspace import Workspace
    # Derive Workspace
    res = await session.execute(select(Workspace).limit(1))
    workspace = res.scalar_one_or_none()
    if not workspace:
        workspace = Workspace(name="Default Workspace")
        session.add(workspace)
        await session.flush()
    workspace_id = workspace.id

    folder_id = None
    if folder_guid is not None:
        folder_result = await session.execute(select(Folder).where(Folder.guid == folder_guid))
        folder = folder_result.scalar_one_or_none()
        if not folder:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Target folder not found",
            )
        folder_id = folder.id
        workspace_id = folder.workspace_id # Override with folder's workspace if available
    
    uploaded_files = []

    for file in files:
        if not file.filename.lower().endswith(".pdf"):
            continue
        storage_filename = f"{uuid.uuid4()}.pdf"
        storage_path = os.path.join(settings.STORAGE_PATH, storage_filename)

        size = 0
        h = hashlib.sha256()
        try:
            async with aiofiles.open(storage_path, "wb") as buffer:
                while content := await file.read(1024 * 1024):
                    size += len(content)
                    h.update(content)
                    await buffer.write(content)
        except Exception as e:
            if os.path.exists(storage_path):
                os.remove(storage_path)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to save file {file.filename}: {str(e)}",
            )
        
        content_hash = h.hexdigest()

        # Deduplication check
        existing_file_query = select(File).where(File.content_hash == content_hash).limit(1)
        existing_file_result = await session.execute(existing_file_query)
        existing_file = existing_file_result.scalar_one_or_none()

        if existing_file and os.path.exists(existing_file.storage_path):
            # Duplicate found physically on disk, reuse path and delete temp
            os.remove(storage_path)
            storage_path = existing_file.storage_path
        original_name = file.filename
        name_base, extension = os.path.splitext(original_name)
        new_name = original_name
        counter = 1
        while True:
            collision_query = select(File).where(
                File.folder_id == folder_id,
                File.name == new_name,
                File.is_deleted == False
            )
            collision_result = await session.execute(collision_query)
            if not collision_result.scalar_one_or_none():
                break
            new_name = f"{name_base} ({counter}){extension}"
            counter += 1
        new_file = File(
            name=new_name,
            storage_path=storage_path,
            size=size,
            folder_id=folder_id,
            workspace_id=workspace_id,
            content_hash=content_hash,
            is_deleted=False,
        )
        session.add(new_file)
        uploaded_files.append(new_file)
    if not uploaded_files:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No valid PDF files provided.",
        )

    await session.commit()
    for f in uploaded_files:
        await session.refresh(f)
    return uploaded_files

@router.get("/{guid}/download")
async def download_file(guid: str, session: SessionDep):

    result = await session.execute(select(File).where(File.guid == guid))
    db_file = result.scalar_one_or_none()
    if not db_file or db_file.is_deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="File not found or has been deleted.",
        )
    if not os.path.exists(db_file.storage_path):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Physical file not found on disk.",
        )
    return FastAPIFileResponse(
        path=db_file.storage_path,
        filename=db_file.name,
        media_type="application/pdf"
    )

@router.patch("/{guid}", response_model=FileResponse)
async def rename_file(guid: str, file_in: FileRename, session: SessionDep):

    if not file_in.name.lower().endswith(".pdf"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Filename must end with .pdf",
        )
    result = await session.execute(select(File).where(File.guid == guid))
    db_file = result.scalar_one_or_none()
    if not db_file or db_file.is_deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="File not found.",
        )
    db_file.name = file_in.name
    await session.commit()
    await session.refresh(db_file)
    return db_file

@router.delete("/{guid}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_file(guid: str, session: SessionDep):

    result = await session.execute(select(File).where(File.guid == guid))
    db_file = result.scalar_one_or_none()
    if not db_file or db_file.is_deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="File not found.",
        )
    db_file.is_deleted = True
    await session.commit()
    return

@router.patch("/{guid}/favorite", response_model=FileResponse)
async def toggle_favorite_file(
    guid: str, favorite_in: FileFavoriteToggle, session: SessionDep
):

    result = await session.execute(select(File).where(File.guid == guid))
    db_file = result.scalar_one_or_none()
    if not db_file or db_file.is_deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="File not found or deleted.",
        )
    db_file.is_favorite = favorite_in.is_favorite
    await session.commit()
    await session.refresh(db_file)
    return db_file
    
@router.post("/{guid}/restore", response_model=FileResponse)
async def restore_file(guid: str, session: SessionDep):

    result = await session.execute(select(File).where(File.guid == guid))
    db_file = result.scalar_one_or_none()
    if not db_file or not db_file.is_deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="File not found or not in trash.",
        )
    db_file.is_deleted = False
    await session.commit()
    await session.refresh(db_file)
    return db_file