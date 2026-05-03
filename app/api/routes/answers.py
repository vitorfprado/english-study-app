from fastapi import APIRouter, Depends, Form, HTTPException, Request
from fastapi.responses import HTMLResponse
from sqlmodel import Session

from app.db.database import get_session
from app.deps import templates
from app.models.answer import Answer
from app.models.exercise import Exercise
from app.services.correction_service import evaluate_answer

router = APIRouter(prefix="/answers", tags=["answers"])


@router.post("", response_class=HTMLResponse)
def submit_answer(
    request: Request,
    db: Session = Depends(get_session),
    exercise_id: int = Form(...),
    user_answer: str = Form(...),
) -> HTMLResponse:
    ex = db.get(Exercise, exercise_id)
    if not ex:
        raise HTTPException(404, "Exercício não encontrado")
    result = evaluate_answer(user_answer, ex.correct_answer, ex.explanation)
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
        "exercises/_answer_result.html",
        {"request": request, "answer": ans, "exercise": ex},
    )
