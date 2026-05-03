from sqlmodel import Session

from app.core.config import get_settings
from app.models.exercise import Exercise
from app.models.material import Material
from app.services import ai_service


async def create_exercise_from_material(db: Session, material: Material) -> Exercise:
    payload = await ai_service.generate_exercise_from_material(material, get_settings())
    ex = Exercise(
        material_id=material.id,
        question=payload.question,
        exercise_type=payload.exercise_type,
        correct_answer=payload.correct_answer,
        explanation=payload.explanation,
    )
    db.add(ex)
    db.commit()
    db.refresh(ex)
    return ex
