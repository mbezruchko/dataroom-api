from datetime import datetime
from typing import Optional
from sqlalchemy import String, Integer, ForeignKey, DateTime, Boolean, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base

class Folder(Base):
    __tablename__ = "folders"

    id: Mapped[int]                    = mapped_column(primary_key=True, index=True)
    name: Mapped[str]                  = mapped_column(String(255), nullable=False)
    parent_id: Mapped[int | None]      = mapped_column(ForeignKey("folders.id", ondelete="CASCADE"), index=True, nullable=True)
    is_favorite: Mapped[bool]          = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime]       = mapped_column(DateTime(timezone=True), server_default=func.now())
    parent: Mapped[Optional["Folder"]] = relationship(
        "Folder",
        back_populates="subfolders",
        remote_side=[id]
    )
    subfolders: Mapped[list["Folder"]] = relationship(
        "Folder",
        back_populates="parent",
        cascade="all"
    )
    files: Mapped[list["File"]] = relationship(
        "File",
        back_populates="folder",
        cascade="all, delete-orphan"
    )