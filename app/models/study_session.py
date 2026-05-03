from datetime import datetime
from typing import Optional

from sqlalchemy import Column, Text
from sqlmodel import Field, SQLModel


class StudySession(SQLModel, table=True):
    __tablename__ = "study_session"

    id: Optional[int] = Field(default=None, primary_key=True)
    title: str = Field(sa_column=Column(Text, nullable=False))
    notes: Optional[str] = Field(default=None, sa_column=Column(Text, nullable=True))
    started_at: Optional[datetime] = Field(default=None)
    finished_at: Optional[datetime] = Field(default=None)
    created_at: datetime = Field(default_factory=datetime.utcnow)
