"""Metadados e imports de modelos para Alembic (autogenerate)."""

from sqlmodel import SQLModel

from app.models import (  # noqa: F401
    Answer,
    DeckStudyRun,
    Exercise,
    ExerciseDeck,
    ExerciseSrs,
    Material,
    StudySession,
)

__all__ = [
    "SQLModel",
    "Answer",
    "DeckStudyRun",
    "Exercise",
    "ExerciseDeck",
    "ExerciseSrs",
    "Material",
    "StudySession",
]
