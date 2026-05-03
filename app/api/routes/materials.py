from datetime import datetime

from fastapi import APIRouter, Depends, Form, HTTPException, Request
from fastapi.responses import HTMLResponse, RedirectResponse, Response
from sqlalchemy import desc
from sqlmodel import Session, select

from app.db.database import get_session
from app.deps import templates
from app.models.enums import DifficultyLevel, SourceType
from app.models.material import Material
from app.services import exercise_generator

router = APIRouter(prefix="/materials", tags=["materials"])

_SOURCE_VALUES = {e.value for e in SourceType}
_DIFF_VALUES = {e.value for e in DifficultyLevel}


def _validate_types(source_type: str, difficulty_level: str) -> None:
    if source_type not in _SOURCE_VALUES:
        raise HTTPException(400, f"source_type inválido: {source_type}")
    if difficulty_level not in _DIFF_VALUES:
        raise HTTPException(400, f"difficulty_level inválido: {difficulty_level}")


@router.get("", response_class=HTMLResponse)
def list_materials(request: Request, db: Session = Depends(get_session)) -> HTMLResponse:
    stmt = select(Material).order_by(desc(Material.id))
    rows = list(db.exec(stmt).all())
    return templates.TemplateResponse(
        "materials/list.html",
        {"request": request, "materials": rows, "title": "Materiais"},
    )


@router.get("/new", response_class=HTMLResponse)
def new_material_form(request: Request) -> HTMLResponse:
    return templates.TemplateResponse(
        "materials/form.html",
        {
            "request": request,
            "material": None,
            "title": "Novo material",
            "source_types": list(SourceType),
            "difficulty_levels": list(DifficultyLevel),
        },
    )


@router.post("")
def create_material(
    request: Request,
    db: Session = Depends(get_session),
    title: str = Form(...),
    description: str | None = Form(None),
    content: str = Form(...),
    source_type: str = Form(...),
    difficulty_level: str = Form(...),
) -> RedirectResponse:
    _validate_types(source_type, difficulty_level)
    row = Material(
        title=title.strip(),
        description=(description or "").strip() or None,
        content=content.strip(),
        source_type=source_type,
        difficulty_level=difficulty_level,
    )
    db.add(row)
    db.commit()
    db.refresh(row)
    return RedirectResponse(url=f"/materials/{row.id}", status_code=303)


@router.get("/{material_id}", response_class=HTMLResponse)
def material_detail(request: Request, material_id: int, db: Session = Depends(get_session)) -> HTMLResponse:
    row = db.get(Material, material_id)
    if not row:
        raise HTTPException(404, "Material não encontrado")
    return templates.TemplateResponse(
        "materials/detail.html",
        {"request": request, "material": row, "title": row.title},
    )


@router.get("/{material_id}/edit", response_class=HTMLResponse)
def edit_material_form(request: Request, material_id: int, db: Session = Depends(get_session)) -> HTMLResponse:
    row = db.get(Material, material_id)
    if not row:
        raise HTTPException(404, "Material não encontrado")
    return templates.TemplateResponse(
        "materials/form.html",
        {
            "request": request,
            "material": row,
            "title": "Editar material",
            "source_types": list(SourceType),
            "difficulty_levels": list(DifficultyLevel),
        },
    )


@router.post("/{material_id}", response_class=HTMLResponse)
def update_material(
    request: Request,
    material_id: int,
    db: Session = Depends(get_session),
    title: str = Form(...),
    description: str | None = Form(None),
    content: str = Form(...),
    source_type: str = Form(...),
    difficulty_level: str = Form(...),
) -> RedirectResponse:
    row = db.get(Material, material_id)
    if not row:
        raise HTTPException(404, "Material não encontrado")
    _validate_types(source_type, difficulty_level)
    row.title = title.strip()
    row.description = (description or "").strip() or None
    row.content = content.strip()
    row.source_type = source_type
    row.difficulty_level = difficulty_level
    row.updated_at = datetime.utcnow()
    db.add(row)
    db.commit()
    return RedirectResponse(url=f"/materials/{material_id}", status_code=303)


@router.post("/{material_id}/delete")
def delete_material(material_id: int, db: Session = Depends(get_session)) -> RedirectResponse:
    row = db.get(Material, material_id)
    if not row:
        raise HTTPException(404, "Material não encontrado")
    db.delete(row)
    db.commit()
    return RedirectResponse(url="/materials", status_code=303)


@router.post("/{material_id}/exercises/generate")
async def generate_exercise_for_material(
    request: Request,
    material_id: int,
    db: Session = Depends(get_session),
) -> Response:
    row = db.get(Material, material_id)
    if not row:
        raise HTTPException(404, "Material não encontrado")
    ex = await exercise_generator.create_exercise_from_material(db, row)
    if request.headers.get("hx-request"):
        return templates.TemplateResponse(
            "materials/_exercise_generated.html",
            {"request": request, "exercise": ex},
        )
    return RedirectResponse(url=f"/exercises/{ex.id}", status_code=303)
