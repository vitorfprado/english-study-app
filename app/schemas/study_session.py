from datetime import datetime

from pydantic import BaseModel, Field


class StudySessionCreate(BaseModel):
    title: str = Field(min_length=1)
    notes: str | None = None
    started_at: datetime | None = None
