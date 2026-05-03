from pathlib import Path

from starlette.templating import Jinja2Templates

_BASE = Path(__file__).resolve().parent
templates = Jinja2Templates(directory=str(_BASE / "templates"))
