from __future__ import annotations

import asyncio

from rq import Connection, Worker
from sqlalchemy import delete
from sqlmodel import Session

from app.core.config import get_settings
from app.core.queue import get_redis_connection
from app.db.database import engine
from app.models.enums import ProcessingStatus
from app.models.exercise import Exercise
from app.models.exercise_deck import ExerciseDeck
from app.models.material import Material
from app.services import ai_service


def generate_deck_for_material(deck_id: int, difficulty_level: str, exercise_type: str) -> None:
    settings = get_settings()
    with Session(engine) as db:
        deck = db.get(ExerciseDeck, deck_id)
        if not deck:
            return
        material = db.get(Material, deck.material_id)
        if not material:
            deck.processing_status = ProcessingStatus.FAILED.value
            deck.processing_error = "Material não encontrado para geração do deck."
            db.add(deck)
            db.commit()
            return

        deck.processing_status = ProcessingStatus.PROCESSING.value
        deck.processing_error = None
        db.add(deck)
        db.commit()

        try:
            count = max(1, int(deck.exercise_count))
            db.exec(delete(Exercise).where(Exercise.deck_id == deck.id))
            db.commit()
            payloads = asyncio.run(
                ai_service.generate_exercise_deck_from_material(
                    material,
                    count,
                    settings,
                    difficulty_level=difficulty_level,
                    exercise_type=exercise_type,
                )
            )
            for p in payloads:
                ex = Exercise(
                    material_id=material.id,
                    deck_id=deck.id,
                    question=p.question,
                    exercise_type=p.exercise_type,
                    correct_answer=p.correct_answer,
                    explanation=p.explanation,
                )
                db.add(ex)
            deck.exercise_count = len(payloads)
            deck.processing_status = ProcessingStatus.COMPLETED.value
            deck.processing_error = None
        except Exception as exc:
            deck.processing_status = ProcessingStatus.FAILED.value
            deck.processing_error = str(exc)[:2000]
        finally:
            db.add(deck)
            db.commit()


def run() -> None:
    settings = get_settings()
    redis_conn = get_redis_connection()
    with Connection(redis_conn):
        worker = Worker([settings.queue_ai_name])
        worker.work(with_scheduler=False)


if __name__ == "__main__":
    run()
