from __future__ import annotations

from datetime import datetime
from typing import Optional

from sqlalchemy import Column, Float, ForeignKey, Integer
from sqlmodel import Field, SQLModel


class ExerciseSrs(SQLModel, table=True):
    """Agendamento simples estilo cartão (revisões futuras). Um registro por exercício."""

    __tablename__ = "exercise_srs"

    exercise_id: int = Field(sa_column=Column(ForeignKey("exercise.id", ondelete="CASCADE"), primary_key=True))
    due_at: datetime = Field(default_factory=datetime.utcnow)
    interval_days: float = Field(default=0.0, sa_column=Column(Float, nullable=False))
    ease: float = Field(default=2.5, sa_column=Column(Float, nullable=False))
    repetitions: int = Field(default=0, sa_column=Column(Integer, nullable=False))
    lapses: int = Field(default=0, sa_column=Column(Integer, nullable=False))
    updated_at: datetime = Field(default_factory=datetime.utcnow)
