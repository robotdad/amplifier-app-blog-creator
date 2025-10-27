"""Template configuration - shared to avoid circular imports."""

from pathlib import Path

from fastapi.templating import Jinja2Templates

template_dir = Path(__file__).parent / "templates"
template_dir.mkdir(exist_ok=True)
templates = Jinja2Templates(directory=str(template_dir))
