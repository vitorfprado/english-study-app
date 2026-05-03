from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING, Optional

from sqlalchemy import Column, String, Text
from sqlmodel import Field, Relationship, SQLModel

if TYPE_CHECKING:
    from app.models.exercise import Exercise


class Material(SQLModel, table=True):
    __tablename__ = "material"

    id: Optional[int] = Field(default=None, primary_key=True)
    title: str = Field(sa_column=Column(String(255), nullable=False))
    description: Optional[str] = Field(default=None, sa_column=Column(Text, nullable=True))
    content: str = Field(sa_column=Column(Text, nullable=False))
    source_type: str = Field(sa_column=Column(String(64), nullable=False))
    difficulty_level: str = Field(sa_column=Column(String(32), nullable=False))
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    exercises: list["Exercise"] = Relationship(back_populates="material")
