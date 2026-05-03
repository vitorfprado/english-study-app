from __future__ import annotations

import json
from datetime import datetime
from typing import Any, Optional

from sqlalchemy import Column, ForeignKey, Text
from sqlmodel import Field, SQLModel


class DeckStudyRun(SQLModel, table=True):
    __tablename__ = "deck_study_run"

    id: Optional[int] = Field(default=None, primary_key=True)
    deck_id: int = Field(sa_column=Column(ForeignKey("exercise_deck.id", ondelete="CASCADE"), nullable=False))
    queue_ids_json: str = Field(sa_column=Column(Text, nullable=False))
    created_at: datetime = Field(default_factory=datetime.utcnow)
    completed_at: Optional[datetime] = Field(default=None)

    def queue_ids(self) -> list[int]:
        raw: Any = json.loads(self.queue_ids_json)
        return [int(x) for x in raw]

    def set_queue_ids(self, ids: list[int]) -> None:
        self.queue_ids_json = json.dumps(ids)
