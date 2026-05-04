from __future__ import annotations

from datetime import datetime
from typing import Optional

from sqlalchemy import Column, ForeignKey, Integer, String, Text
from sqlmodel import Field, SQLModel

from app.models.enums import ProcessingStatus


class ExerciseDeck(SQLModel, table=True):
    __tablename__ = "exercise_deck"

    id: Optional[int] = Field(default=None, primary_key=True)
    material_id: int = Field(sa_column=Column(ForeignKey("material.id", ondelete="CASCADE"), nullable=False))
    title: str = Field(sa_column=Column(Text, nullable=False))
    exercise_count: int = Field(default=0, sa_column=Column(Integer, nullable=False))
    processing_status: str = Field(
        default=ProcessingStatus.COMPLETED.value,
        sa_column=Column(String(32), nullable=False, default=ProcessingStatus.COMPLETED.value),
    )
    processing_error: Optional[str] = Field(default=None, sa_column=Column(Text, nullable=True))
    created_at: datetime = Field(default_factory=datetime.utcnow)
