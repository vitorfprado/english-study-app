from datetime import datetime

from sqlmodel import Session

from app.core.config import get_settings
from app.models.exercise import Exercise
from app.models.exercise_deck import ExerciseDeck
from app.models.material import Material
from app.services import ai_service


async def create_exercise_from_material(db: Session, material: Material) -> Exercise:
    payload = await ai_service.generate_exercise_from_material(material, get_settings())
    ex = Exercise(
        material_id=material.id,
        deck_id=None,
        question=payload.question,
        exercise_type=payload.exercise_type,
        correct_answer=payload.correct_answer,
        explanation=payload.explanation,
    )
    db.add(ex)
    db.commit()
    db.refresh(ex)
    return ex


async def create_deck_from_material(
    db: Session,
    material: Material,
    count: int,
    deck_title: str | None = None,
    difficulty_level: str = "intermediate",
    exercise_type: str = "mixed",
) -> ExerciseDeck:
    settings = get_settings()
    count = max(1, min(count, settings.max_deck_size))
    payloads = await ai_service.generate_exercise_deck_from_material(
        material,
        count,
        settings,
        difficulty_level=difficulty_level,
        exercise_type=exercise_type,
    )
    resolved_title = (deck_title or "").strip()
    if not resolved_title:
        resolved_title = f"Deck · {material.title} · {datetime.utcnow().strftime('%Y-%m-%d %H:%M')}"
    deck = ExerciseDeck(
        material_id=material.id,
        title=resolved_title[:500],
        exercise_count=len(payloads),
    )
    db.add(deck)
    db.commit()
    db.refresh(deck)
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
    db.commit()
    db.refresh(deck)
    return deck
