import re
import logging
from io import BytesIO
from pathlib import Path

from pypdf import PdfReader

from app.core.config import get_settings
from app.services.ocr_service import extract_text_with_ocr

logger = logging.getLogger(__name__)


def extract_text_from_pdf_bytes(data: bytes) -> str:
    settings = get_settings()
    native_text = _extract_native_text(data)
    if _is_good_enough(native_text):
        logger.info("PDF extraido com estrategia nativa (pypdf).")
        return _truncate_text(native_text)

    logger.info("Texto nativo insuficiente; iniciando fallback OCR local.")
    ocr_text = extract_text_with_ocr(data, languages=settings.ocr_languages)
    if _is_good_enough(ocr_text):
        logger.info("PDF extraido com sucesso por fallback OCR.")
        return _truncate_text(ocr_text)

    logger.warning("Falha total na extracao de texto do PDF (nativo + OCR).")
    raise ValueError(
        "Não foi possível extrair texto do PDF. "
        "O arquivo pode estar vazio, ilegível ou com baixa qualidade para OCR."
    )


def _extract_native_text(data: bytes) -> str:
    reader = PdfReader(BytesIO(data))
    parts: list[str] = []
    for page in reader.pages:
        page_text = page.extract_text()
        if page_text and page_text.strip():
            parts.append(page_text.strip())
    return "\n\n".join(parts).strip()


def _is_good_enough(text: str | None) -> bool:
    if not text:
        return False
    return len(text.strip()) >= get_settings().min_extracted_chars


def _truncate_text(text: str) -> str:
    max_chars = get_settings().max_extracted_chars
    if len(text) > max_chars:
        return text[:max_chars] + "\n\n[… texto truncado ao limite configurado …]"
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
