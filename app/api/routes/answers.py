from fastapi import APIRouter, Depends, Form, HTTPException, Request
from fastapi.responses import HTMLResponse
from sqlmodel import Session

from app.core.config import get_settings
from app.db.database import get_session
from app.deps import templates
from app.models.answer import Answer
from app.models.exercise import Exercise
from app.services import ai_service

router = APIRouter(prefix="/answers", tags=["answers"])


@router.post("", response_class=HTMLResponse)
async def submit_answer(
    request: Request,
    db: Session = Depends(get_session),
    exercise_id: int = Form(...),
    user_answer: str = Form(...),
) -> HTMLResponse:
    ex = db.get(Exercise, exercise_id)
    if not ex:
        raise HTTPException(404, "Exercício não encontrado")
    result, used_ai = await ai_service.evaluate_submitted_answer_with_fallback(
        question=ex.question,
        exercise_type=ex.exercise_type,
        reference_answer=ex.correct_answer,
        user_answer=user_answer,
        exercise_explanation=ex.explanation,
        settings=get_settings(),
    )
    ans = Answer(
        exercise_id=exercise_id,
        user_answer=user_answer.strip(),
        is_correct=result.is_correct,
        feedback=result.feedback,
    )
    db.add(ans)
    db.commit()
    db.refresh(ans)
    return templates.TemplateResponse(
        request,
        "exercises/_answer_result.html",
        {"answer": ans, "exercise": ex, "used_ai_correction": used_ai},
    )
