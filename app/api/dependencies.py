from typing import Annotated, Optional
from fastapi import Depends, HTTPException, status, Header, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.core.database import get_db
from app.models.workspace import Workspace

SessionDep = Annotated[AsyncSession, Depends(get_db)]

def get_session_guid(
    session_guid_header: Optional[str] = Header(None, alias="session-guid"),
    session_guid_query: Optional[str] = Query(None, alias="session-guid")
) -> Optional[str]:
    return session_guid_header or session_guid_query

SessionGuidDep = Annotated[Optional[str], Depends(get_session_guid)]

async def check_workspace_access(
    workspace: Workspace, 
    session_guid: Optional[str]
) -> None:
    if workspace.session_guid and workspace.session_guid != session_guid:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, 
            detail="You don't have access to this workspace"
        )