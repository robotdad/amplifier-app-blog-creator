"""Session management routes."""

import logging
from pathlib import Path
from typing import Annotated

from fastapi import APIRouter
from fastapi import Form
from fastapi import Request
from fastapi.responses import HTMLResponse
from fastapi.responses import RedirectResponse
from pydantic import BaseModel

from ...session import SessionManager
from ..templates_config import templates

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/sessions")


class PathValidationRequest(BaseModel):
    path: str
    type: str  # "file" or "directory"


class PathValidationResponse(BaseModel):
    valid: bool
    type: str | None = None
    word_count: int | None = None
    file_count: int | None = None
    error: str | None = None


@router.get("/new", response_class=HTMLResponse)
async def new_session(request: Request):
    """Create new session and show setup page."""
    # Create session
    session_mgr = SessionManager()
    request.session["session_id"] = session_mgr.state.session_id

    return templates.TemplateResponse(
        "setup.html",
        {
            "request": request,
            "session_id": session_mgr.state.session_id,
        },
    )


@router.post("/{session_id}/validate-path")
async def validate_path(
    session_id: str,
    path: Annotated[str, Form()],
    type: Annotated[str, Form()],
):
    """Validate file or directory path."""
    try:
        p = Path(path).expanduser()

        if not p.exists():
            return HTMLResponse(
                """<div class="feedback feedback-invalid">
                    <span class="feedback-icon">⚠</span>
                    Path does not exist
                </div>""",
                status_code=200,
            )

        if type == "file":
            if not p.is_file():
                return HTMLResponse(
                    """<div class="feedback feedback-invalid">
                        <span class="feedback-icon">⚠</span>
                        Path is not a file
                    </div>""",
                    status_code=200,
                )

            if p.suffix not in [".md", ".txt"]:
                return HTMLResponse(
                    """<div class="feedback feedback-invalid">
                        <span class="feedback-icon">⚠</span>
                        File must be .md or .txt
                    </div>""",
                    status_code=200,
                )

            content = p.read_text()
            word_count = len(content.split())

            return HTMLResponse(
                f"""<div class="feedback feedback-valid">
                    <span class="feedback-icon">✓</span>
                    Valid - {word_count} words
                </div>""",
                status_code=200,
            )

        if type == "directory":
            if not p.is_dir():
                return HTMLResponse(
                    """<div class="feedback feedback-invalid">
                        <span class="feedback-icon">⚠</span>
                        Path is not a directory
                    </div>""",
                    status_code=200,
                )

            md_files = list(p.glob("*.md"))
            file_count = len(md_files)

            if file_count == 0:
                return HTMLResponse(
                    """<div class="feedback feedback-invalid">
                        <span class="feedback-icon">⚠</span>
                        No .md files found
                    </div>""",
                    status_code=200,
                )

            return HTMLResponse(
                f"""<div class="feedback feedback-valid">
                    <span class="feedback-icon">✓</span>
                    Valid - {file_count} samples found
                </div>""",
                status_code=200,
            )

    except Exception as e:
        logger.error(f"Path validation error: {e}")
        return HTMLResponse(
            f"""<div class="feedback feedback-invalid">
                <span class="feedback-icon">⚠</span>
                Error: {str(e)}
            </div>""",
            status_code=500,
        )


@router.post("/{session_id}/start-workflow")
async def start_workflow(
    request: Request,
    session_id: str,
    idea_path: Annotated[str, Form()],
    writings_dir: Annotated[str, Form()],
    instructions: Annotated[str | None, Form()] = None,
):
    """Start the blog creation workflow."""
    # Store paths in session for progress stage
    session_mgr = SessionManager(Path(f".data/blog_creator/{session_id}"))
    session_mgr.state.idea_path = idea_path
    session_mgr.state.writings_dir = writings_dir
    if instructions:
        session_mgr.state.additional_instructions = instructions
    session_mgr.save()

    # Redirect to progress page
    return RedirectResponse(f"/sessions/{session_id}/progress", status_code=303)
