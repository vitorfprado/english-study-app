from datetime import datetime

from fastapi import APIRouter, Depends, Form, HTTPException, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from sqlmodel import Session

from app.db.database import get_session
from app.deps import templates
from app.models.study_session import StudySession
from app.services import study_service

router = APIRouter(prefix="/study-sessions", tags=["study_sessions"])


@router.get("", response_class=HTMLResponse)
def list_study_sessions(request: Request, db: Session = Depends(get_session)) -> HTMLResponse:
    rows = study_service.list_sessions(db)
    return templates.TemplateResponse(
        request,
        "study_sessions/list.html",
        {"sessions": rows, "title": "Sessões de estudo"},
    )


@router.get("/new", response_class=HTMLResponse)
def new_session_form(request: Request) -> HTMLResponse:
    return templates.TemplateResponse(
        request,
        "study_sessions/form.html",
        {"title": "Nova sessão"},
    )


@router.post("")
def create_study_session(
    db: Session = Depends(get_session),
    title: str = Form(...),
    notes: str | None = Form(None),
) -> RedirectResponse:
    row = study_service.create_session(db, title.strip(), (notes or "").strip() or None, datetime.utcnow())
    return RedirectResponse(url="/study-sessions", status_code=303)


@router.post("/{session_id}/finish")
def finish_study_session(session_id: int, db: Session = Depends(get_session)) -> RedirectResponse:
    row = study_service.get_session_by_id(db, session_id)
    if not row:
        raise HTTPException(404, "Sessão não encontrada")
    study_service.finish_session(db, row)
    return RedirectResponse(url="/study-sessions", status_code=303)
