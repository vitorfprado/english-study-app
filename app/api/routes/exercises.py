from fastapi import APIRouter, Depends, Form, HTTPException, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from sqlalchemy import desc
from sqlmodel import Session, select

from app.db.database import get_session
from app.deps import templates
from app.models.answer import Answer
from app.models.enums import ExerciseType
from app.models.exercise import Exercise
from app.models.material import Material

router = APIRouter(prefix="/exercises", tags=["exercises"])

_EX_TYPES = {e.value for e in ExerciseType}


def _validate_exercise_type(exercise_type: str) -> None:
    if exercise_type not in _EX_TYPES:
        raise HTTPException(400, f"exercise_type inválido: {exercise_type}")


@router.get("", response_class=HTMLResponse)
def list_exercises(request: Request, db: Session = Depends(get_session)) -> HTMLResponse:
    stmt = select(Exercise).order_by(desc(Exercise.id))
    rows = list(db.exec(stmt).all())
    material_ids = {r.material_id for r in rows if r.material_id}
    materials = {}
    for mid in material_ids:
        m = db.get(Material, mid)
        if m:
            materials[mid] = m.title
    return templates.TemplateResponse(
        "exercises/list.html",
        {"request": request, "exercises": rows, "material_titles": materials, "title": "Exercícios"},
    )


@router.get("/new", response_class=HTMLResponse)
def new_exercise_form(request: Request, db: Session = Depends(get_session), material_id: int | None = None) -> HTMLResponse:
    stmt = select(Material).order_by(desc(Material.id))
    materials = list(db.exec(stmt).all())
    return templates.TemplateResponse(
        "exercises/form.html",
        {
            "request": request,
            "materials": materials,
            "prefill_material_id": material_id,
            "title": "Novo exercício (manual)",
            "exercise_types": list(ExerciseType),
        },
    )


@router.post("")
def create_exercise(
    db: Session = Depends(get_session),
    question: str = Form(...),
    exercise_type: str = Form(...),
    correct_answer: str = Form(...),
    explanation: str | None = Form(None),
    material_id: str | None = Form(None),
) -> RedirectResponse:
    _validate_exercise_type(exercise_type)
    mid: int | None = None
    if material_id and material_id.strip():
        mid = int(material_id)
        if not db.get(Material, mid):
            raise HTTPException(400, "Material não encontrado")
    row = Exercise(
        material_id=mid,
        question=question.strip(),
        exercise_type=exercise_type,
        correct_answer=correct_answer.strip(),
        explanation=(explanation or "").strip() or None,
    )
    db.add(row)
    db.commit()
    db.refresh(row)
    return RedirectResponse(url=f"/exercises/{row.id}", status_code=303)


@router.get("/{exercise_id}", response_class=HTMLResponse)
def exercise_detail(request: Request, exercise_id: int, db: Session = Depends(get_session)) -> HTMLResponse:
    row = db.get(Exercise, exercise_id)
    if not row:
        raise HTTPException(404, "Exercício não encontrado")
    material = db.get(Material, row.material_id) if row.material_id else None

    stmt = select(Answer).where(Answer.exercise_id == exercise_id).order_by(desc(Answer.id))  # type: ignore[arg-type]
    answers = list(db.exec(stmt).all())
    return templates.TemplateResponse(
        "exercises/detail.html",
        {
            "request": request,
            "exercise": row,
            "material": material,
            "answers": answers,
            "title": f"Exercício #{row.id}",
        },
    )
