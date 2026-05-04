from __future__ import annotations

from redis import Redis
from rq import Queue
from rq.job import Job

from app.core.config import get_settings


def get_redis_connection() -> Redis:
    settings = get_settings()
    return Redis.from_url(settings.redis_url)


def get_pdf_queue() -> Queue:
    settings = get_settings()
    return Queue(name=settings.queue_pdf_name, connection=get_redis_connection())


def get_ai_queue() -> Queue:
    settings = get_settings()
    return Queue(name=settings.queue_ai_name, connection=get_redis_connection())


def enqueue_pdf_job(material_id: int) -> Job:
    return get_pdf_queue().enqueue("app.workers.pdf_worker.process_material_pdf", material_id)


def enqueue_deck_generation_job(deck_id: int, difficulty_level: str, exercise_type: str) -> Job:
    return get_ai_queue().enqueue(
        "app.workers.ai_worker.generate_deck_for_material",
        deck_id,
        difficulty_level,
        exercise_type,
    )
