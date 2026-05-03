"""Metadados e imports de modelos para Alembic (autogenerate)."""

from sqlmodel import SQLModel

from app.models import Answer, Exercise, Material, StudySession  # noqa: F401

__all__ = ["SQLModel", "Answer", "Exercise", "Material", "StudySession"]
