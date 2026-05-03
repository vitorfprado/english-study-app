import re
from io import BytesIO
from pathlib import Path

from pypdf import PdfReader

from app.core.config import get_settings


def extract_text_from_pdf_bytes(data: bytes) -> str:
    reader = PdfReader(BytesIO(data))
    parts: list[str] = []
    for page in reader.pages:
        t = page.extract_text()
        if t and t.strip():
            parts.append(t.strip())
    text = "\n\n".join(parts).strip()
    if not text:
        raise ValueError(
            "Não foi possível extrair texto do PDF. "
            "Pode ser um arquivo só com imagens (sem OCR neste MVP) ou PDF vazio."
        )
    max_chars = get_settings().max_extracted_chars
    if len(text) > max_chars:
        text = text[:max_chars] + "\n\n[… texto truncado ao limite configurado …]"
    return text


def safe_pdf_filename(original: str) -> str:
    name = Path(original).name
    stem = re.sub(r"[^a-zA-Z0-9._-]", "_", Path(name).stem).strip("._") or "aula"
    return f"{stem[:72]}.pdf"


def material_pdf_relative_path(material_id: int, safe_name: str) -> str:
    return f"materials/{material_id}_{safe_name}"


def write_material_pdf(material_id: int, pdf_bytes: bytes, original_filename: str) -> str:
    settings = get_settings()
    base = Path(settings.upload_dir)
    dest_dir = base / "materials"
    dest_dir.mkdir(parents=True, exist_ok=True)
    safe = safe_pdf_filename(original_filename)
    rel = material_pdf_relative_path(material_id, safe)
    full = base / rel
    full.write_bytes(pdf_bytes)
    return rel


def delete_material_pdf_if_exists(relative_path: str | None) -> None:
    if not relative_path:
        return
    settings = get_settings()
    full = Path(settings.upload_dir) / relative_path
    if full.is_file():
        full.unlink()
