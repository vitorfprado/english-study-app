from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING, Optional

from sqlalchemy import Column, ForeignKey, String, Text
from sqlmodel import Field, Relationship, SQLModel

if TYPE_CHECKING:
    from app.models.answer import Answer
    from app.models.material import Material


class Exercise(SQLModel, table=True):
    __tablename__ = "exercise"

    id: Optional[int] = Field(default=None, primary_key=True)
    material_id: Optional[int] = Field(
        default=None,
        sa_column=Column(ForeignKey("material.id", ondelete="SET NULL"), nullable=True),
    )
    question: str = Field(sa_column=Column(Text, nullable=False))
    exercise_type: str = Field(sa_column=Column(String(64), nullable=False))
    correct_answer: str = Field(sa_column=Column(Text, nullable=False))
    explanation: Optional[str] = Field(default=None, sa_column=Column(Text, nullable=True))
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    material: Optional["Material"] = Relationship(back_populates="exercises")
    answers: list["Answer"] = Relationship(back_populates="exercise")
