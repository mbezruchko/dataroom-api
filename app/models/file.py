import uuid
from datetime import datetime
from sqlalchemy import String, Integer, ForeignKey, DateTime, Boolean, BigInteger, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base

class File(Base):
    __tablename__ = "files"

    id: Mapped[int]                  = mapped_column(primary_key=True, index=True)
    guid: Mapped[str]                = mapped_column(String(36), default=lambda: str(uuid.uuid4()), index=True, unique=True)
    workspace_id: Mapped[int]        = mapped_column(ForeignKey("workspaces.id", ondelete="CASCADE"), index=True, nullable=False)
    name: Mapped[str]                = mapped_column(String(255), nullable=False)
    storage_path: Mapped[str]        = mapped_column(Text, nullable=False)
    size: Mapped[int | None]         = mapped_column(BigInteger, nullable=True)
    folder_id: Mapped[int | None]    = mapped_column(ForeignKey("folders.id", ondelete="CASCADE"), index=True, nullable=True)
    content_hash: Mapped[str | None] = mapped_column(String(64), index=True, nullable=True)
    is_deleted: Mapped[bool]         = mapped_column(Boolean, default=False, index=True)
    is_favorite: Mapped[bool]        = mapped_column(Boolean, default=False, index=True)
    created_at: Mapped[datetime]     = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime]     = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    folder: Mapped["Folder"]         = relationship("Folder", back_populates="files")
    workspace: Mapped["Workspace"]   = relationship("Workspace", back_populates="files")