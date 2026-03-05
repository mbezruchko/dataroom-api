import uuid
from datetime import datetime
from sqlalchemy import String, Text, DateTime, Boolean, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base

class Workspace(Base):
    __tablename__ = "workspaces"

    id: Mapped[int]                 = mapped_column(primary_key=True, index=True)
    guid: Mapped[str]               = mapped_column(String(36), default=lambda: str(uuid.uuid4()), index=True, unique=True)
    name: Mapped[str]               = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime]    = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime]    = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    session_guid: Mapped[str | None] = mapped_column(String(36), index=True, nullable=True)

    folders: Mapped[list["Folder"]] = relationship("Folder", back_populates="workspace", cascade="all, delete-orphan")
    files: Mapped[list["File"]] = relationship("File", back_populates="workspace", cascade="all, delete-orphan")
