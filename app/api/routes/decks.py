from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from sqlalchemy import desc
from sqlmodel import Session, select

from app.db.database import get_session
from app.deps import templates
from app.models.exercise_deck import ExerciseDeck
from app.models.material import Material

router = APIRouter(prefix="/decks", tags=["decks"])


@router.get("", response_class=HTMLResponse)
def list_decks(request: Request, db: Session = Depends(get_session)) -> HTMLResponse:
    stmt = select(ExerciseDeck).order_by(desc(ExerciseDeck.id))  # type: ignore[arg-type]
    decks = list(db.exec(stmt).all())
    titles: dict[int, str] = {}
    for d in decks:
        if d.material_id not in titles:
            mat = db.get(Material, d.material_id)
            titles[d.material_id] = mat.title if mat else f"Material #{d.material_id}"
    return templates.TemplateResponse(
        request,
        "decks/list.html",
        {
            "title": "Meus decks",
            "decks": decks,
            "material_titles": titles,
        },
    )


@router.post("/{deck_id}/delete")
def delete_deck(deck_id: int, db: Session = Depends(get_session)) -> RedirectResponse:
    row = db.get(ExerciseDeck, deck_id)
    if not row:
        raise HTTPException(404, "Deck não encontrado")
    db.delete(row)
    db.commit()
    return RedirectResponse(url="/decks?msg=Deck+removido.", status_code=303)
