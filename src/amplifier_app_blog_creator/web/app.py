"""FastAPI application for blog creator web interface."""

import logging
from contextlib import asynccontextmanager
from pathlib import Path

from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi import Request
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from starlette.middleware.sessions import SessionMiddleware

from .routes import configuration

logger = logging.getLogger(__name__)

load_dotenv()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup/shutdown lifecycle."""
    logger.info("Blog Creator web server started")
    yield
    logger.info("Blog Creator web server shutting down")


app = FastAPI(lifespan=lifespan)

app.add_middleware(SessionMiddleware, secret_key="blog-creator-session-key", max_age=1800)

static_dir = Path(__file__).parent / "static"
static_dir.mkdir(exist_ok=True)
app.mount("/static", StaticFiles(directory=str(static_dir)), name="static")

template_dir = Path(__file__).parent / "templates"
template_dir.mkdir(exist_ok=True)
templates = Jinja2Templates(directory=str(template_dir))

# Include routers
app.include_router(configuration.router)


@app.get("/test")
async def test_page(request: Request):
    """Test route to verify templates and design system."""
    return templates.TemplateResponse(
        "base.html", {"request": request, "show_stage_indicator": True, "current_stage": "Setup"}
    )
