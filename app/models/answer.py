from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING, Optional

from sqlalchemy import Column, ForeignKey, Text
from sqlmodel import Field, Relationship, SQLModel

if TYPE_CHECKING:
    from app.models.exercise import Exercise


class Answer(SQLModel, table=True):
    __tablename__ = "answer"

    id: Optional[int] = Field(default=None, primary_key=True)
    exercise_id: int = Field(sa_column=Column(ForeignKey("exercise.id", ondelete="CASCADE"), nullable=False))
    user_answer: str = Field(sa_column=Column(Text, nullable=False))
    is_correct: bool = Field(default=False)
    feedback: Optional[str] = Field(default=None, sa_column=Column(Text, nullable=True))
    created_at: datetime = Field(default_factory=datetime.utcnow)

    exercise: Optional["Exercise"] = Relationship(back_populates="answers")
