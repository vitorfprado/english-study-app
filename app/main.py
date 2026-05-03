from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles

from app.api.routes import answers, deck_study, decks, exercises, materials, study_sessions
from app.core.config import get_settings
from app.core.logging import configure_logging
from app.deps import templates

configure_logging()
_settings = get_settings()
templates.env.globals["app_name"] = _settings.app_name

app = FastAPI(title=_settings.app_name)

_BASE = Path(__file__).resolve().parent
app.mount("/static", StaticFiles(directory=str(_BASE / "static")), name="static")

app.include_router(materials.router)
app.include_router(decks.router)
app.include_router(deck_study.router)
app.include_router(exercises.router)
app.include_router(answers.router)
app.include_router(study_sessions.router)


@app.get("/", response_class=HTMLResponse)
def index(request: Request) -> HTMLResponse:
    return templates.TemplateResponse(
        request,
        "index.html",
        {"title": "Início", "app_name": _settings.app_name},
    )
