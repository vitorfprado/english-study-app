from __future__ import annotations

from datetime import datetime
from pathlib import Path

from rq import Connection, Worker
from sqlmodel import Session

from app.core.config import get_settings
from app.core.queue import get_redis_connection
from app.db.database import engine
from app.models.enums import ProcessingStatus
from app.models.material import Material
from app.services import pdf_service


def process_material_pdf(material_id: int) -> None:
    with Session(engine) as db:
        material = db.get(Material, material_id)
        if not material:
            return
        material.processing_status = ProcessingStatus.PROCESSING.value
        material.processing_error = None
        material.updated_at = datetime.utcnow()
        db.add(material)
        db.commit()

        try:
            if not material.pdf_stored_path:
                raise ValueError("material sem caminho de PDF salvo")
            pdf_path = Path(get_settings().upload_dir) / material.pdf_stored_path
            if not pdf_path.is_file():
                raise FileNotFoundError(f"arquivo não encontrado: {pdf_path}")
            text = pdf_service.extract_text_from_pdf_bytes(pdf_path.read_bytes())
            material.content = text
            material.processing_status = ProcessingStatus.COMPLETED.value
            material.processing_error = None
        except Exception as exc:
            material.processing_status = ProcessingStatus.FAILED.value
            material.processing_error = str(exc)[:2000]
        finally:
            material.updated_at = datetime.utcnow()
            db.add(material)
            db.commit()


def run() -> None:
    settings = get_settings()
    redis_conn = get_redis_connection()
    with Connection(redis_conn):
        worker = Worker([settings.queue_pdf_name])
        worker.work(with_scheduler=False)


if __name__ == "__main__":
    run()
