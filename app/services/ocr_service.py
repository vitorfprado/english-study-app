from io import BytesIO

import fitz
import pytesseract
from PIL import Image


def extract_text_with_ocr(data: bytes, *, languages: str = "eng+por", zoom: float = 2.0) -> str:
    parts: list[str] = []
    doc = fitz.open(stream=data, filetype="pdf")
    try:
        for page_number, page in enumerate(doc, start=1):
            pix = page.get_pixmap(matrix=fitz.Matrix(zoom, zoom), alpha=False)
            image = Image.open(BytesIO(pix.tobytes("png")))
            page_text = pytesseract.image_to_string(image, lang=languages, config="--psm 6")
            cleaned = page_text.strip()
            if cleaned:
                parts.append(f"[Pagina {page_number}]\n{cleaned}")
    finally:
        doc.close()
    return "\n\n".join(parts).strip()
