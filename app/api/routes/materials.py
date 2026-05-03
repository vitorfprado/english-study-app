from datetime import datetime

from fastapi import APIRouter, Depends, File, Form, HTTPException, Request, UploadFile
from fastapi.responses import HTMLResponse, RedirectResponse, Response
from sqlalchemy import desc
from sqlmodel import Session, select

from app.db.database import get_session
from app.deps import templates
from app.core.config import get_settings
from app.models.enums import DifficultyLevel, ExerciseType, SourceType
from app.models.exercise_deck import ExerciseDeck
from app.models.material import Material
from app.services import exercise_generator, pdf_service

router = APIRouter(prefix="/materials", tags=["materials"])

_SOURCE_VALUES = {e.value for e in SourceType}
_DIFF_VALUES = {e.value for e in DifficultyLevel}
_EX_TYPES = {e.value for e in ExerciseType}


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
        request,
        "materials/list.html",
        {"materials": rows, "title": "Materiais"},
    )


@router.get("/new", response_class=HTMLResponse)
def new_material_form(request: Request) -> HTMLResponse:
    return templates.TemplateResponse(
        request,
        "materials/form.html",
        {
            "material": None,
            "title": "Novo material",
            "source_types": list(SourceType),
            "difficulty_levels": list(DifficultyLevel),
        },
    )


@router.get("/from-pdf", response_class=HTMLResponse)
def upload_pdf_form(request: Request) -> HTMLResponse:
    s = get_settings()
    return templates.TemplateResponse(
        request,
        "materials/from_pdf.html",
        {
            "title": "Importar PDF da aula",
            "default_deck_size": s.default_deck_size,
            "max_deck_size": s.max_deck_size,
            "max_pdf_mb": s.max_pdf_bytes // (1024 * 1024),
        },
    )


@router.post("/from-pdf")
async def create_material_from_pdf(
    request: Request,
    db: Session = Depends(get_session),
    file: UploadFile = File(...),
    title: str | None = Form(None),
) -> RedirectResponse:
    if not file.filename or not file.filename.lower().endswith(".pdf"):
        raise HTTPException(400, "Envie um arquivo .pdf")
    settings = get_settings()
    data = await file.read()
    if len(data) > settings.max_pdf_bytes:
        raise HTTPException(413, f"PDF acima do limite de {settings.max_pdf_bytes // (1024 * 1024)} MB")
    try:
        text = pdf_service.extract_text_from_pdf_bytes(data)
    except ValueError as e:
        raise HTTPException(400, str(e)) from e

    row = Material(
        title=(title or "").strip() or pdf_service.safe_pdf_filename(file.filename).replace(".pdf", "").replace("_", " ")[:200],
        description=f"Importado do PDF: {file.filename}",
        content=text,
        source_type=SourceType.CLASS_SUMMARY.value,
        difficulty_level=DifficultyLevel.INTERMEDIATE.value,
        pdf_original_name=file.filename[:500],
        pdf_stored_path=None,
    )
    db.add(row)
    db.commit()
    db.refresh(row)
    try:
        rel = pdf_service.write_material_pdf(row.id, data, file.filename)
    except OSError:
        db.delete(row)
        db.commit()
        raise HTTPException(500, "Falha ao salvar o PDF no disco") from None
    row.pdf_stored_path = rel
    db.add(row)
    db.commit()
    return RedirectResponse(url=f"/materials/{row.id}?msg=pdf-importado", status_code=303)


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
    stmt = select(ExerciseDeck).where(ExerciseDeck.material_id == material_id).order_by(desc(ExerciseDeck.id)).limit(12)  # type: ignore[arg-type]
    decks = list(db.exec(stmt).all())
    s = get_settings()
    return templates.TemplateResponse(
        request,
        "materials/detail.html",
        {
            "material": row,
            "title": row.title,
            "decks": decks,
            "default_deck_size": s.default_deck_size,
            "max_deck_size": s.max_deck_size,
            "difficulty_levels": list(DifficultyLevel),
            "exercise_types": list(ExerciseType),
        },
    )


@router.get("/{material_id}/edit", response_class=HTMLResponse)
def edit_material_form(request: Request, material_id: int, db: Session = Depends(get_session)) -> HTMLResponse:
    row = db.get(Material, material_id)
    if not row:
        raise HTTPException(404, "Material não encontrado")
    return templates.TemplateResponse(
        request,
        "materials/form.html",
        {
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
    pdf_service.delete_material_pdf_if_exists(row.pdf_stored_path)
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
    deck = await exercise_generator.create_deck_from_material(db, row, 1)
    if request.headers.get("hx-request"):
        return templates.TemplateResponse(
            request,
            "materials/_deck_generated.html",
            {"deck": deck, "material": row},
        )
    return RedirectResponse(url=f"/study/decks/{deck.id}/start", status_code=303)


@router.post("/{material_id}/decks/generate")
async def generate_deck_for_material(
    request: Request,
    material_id: int,
    db: Session = Depends(get_session),
    count: int = Form(...),
    deck_title: str | None = Form(None),
    difficulty_level: str = Form(DifficultyLevel.INTERMEDIATE.value),
    exercise_type: str = Form("mixed"),
) -> Response:
    row = db.get(Material, material_id)
    if not row:
        raise HTTPException(404, "Material não encontrado")
    s = get_settings()
    count = max(1, min(int(count), s.max_deck_size))
    if difficulty_level not in _DIFF_VALUES:
        raise HTTPException(400, f"difficulty_level inválido: {difficulty_level}")
    if exercise_type != "mixed" and exercise_type not in _EX_TYPES:
        raise HTTPException(400, f"exercise_type inválido: {exercise_type}")
    deck = await exercise_generator.create_deck_from_material(
        db,
        row,
        count,
        deck_title=deck_title,
        difficulty_level=difficulty_level,
        exercise_type=exercise_type,
    )
    if request.headers.get("hx-request"):
        return templates.TemplateResponse(
            request,
            "materials/_deck_generated.html",
            {"deck": deck, "material": row},
        )
    return RedirectResponse(url=f"/exercises?deck_id={deck.id}", status_code=303)
