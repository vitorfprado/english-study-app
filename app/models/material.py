from __future__ import annotations

from datetime import datetime
from typing import Optional

from sqlalchemy import Column, String, Text
from sqlmodel import Field, SQLModel


class Material(SQLModel, table=True):
    __tablename__ = "material"

    id: Optional[int] = Field(default=None, primary_key=True)
    title: str = Field(sa_column=Column(String(255), nullable=False))
    description: Optional[str] = Field(default=None, sa_column=Column(Text, nullable=True))
    content: str = Field(sa_column=Column(Text, nullable=False))
    source_type: str = Field(sa_column=Column(String(64), nullable=False))
    difficulty_level: str = Field(sa_column=Column(String(32), nullable=False))
    pdf_original_name: Optional[str] = Field(default=None, sa_column=Column(String(512), nullable=True))
    pdf_stored_path: Optional[str] = Field(default=None, sa_column=Column(String(512), nullable=True))
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
