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


@router.get("/recent-paths")
async def get_recent_paths():
    """Get recent file/folder paths from previous sessions."""
    recent_ideas = []
    recent_writings = []

    sessions_dir = Path(".data/blog_creator")
    if sessions_dir.exists():
        for session_dir in sessions_dir.iterdir():
            if session_dir.is_dir():
                state_file = session_dir / "state.json"
                if state_file.exists():
                    try:
                        import json

                        state = json.loads(state_file.read_text())
                        if state.get("idea_path"):
                            recent_ideas.append(state["idea_path"])
                        if state.get("writings_dir"):
                            recent_writings.append(state["writings_dir"])
                    except Exception:
                        pass

    # Return unique paths, most recent first (reversed)
    return {
        "idea_files": list(dict.fromkeys(reversed(recent_ideas)))[:10],
        "writings_dirs": list(dict.fromkeys(reversed(recent_writings)))[:10],
    }


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
    # Ensure API key is configured before allowing workflow
    from .configuration import is_configured

    if not is_configured(request):
        return RedirectResponse(url="/configure", status_code=302)

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
    request: Request,
    session_id: str,
    type: str,  # From query parameter
):
    """Validate file or directory path."""
    try:
        # Get form data
        form_data = await request.form()

        # HTMX sends whichever input triggered - get the value
        # It could be in idea_path, writings_dir, or just the first form value
        path = (
            form_data.get("idea_path")
            or form_data.get("writings_dir")
            or
            # Fallback: get first value from form
            (list(form_data.values())[0] if form_data else "")
        )

        logger.info(f"Validation: type={type}, path={path}")

        if not path or not type:
            return HTMLResponse(
                """<div class="feedback feedback-invalid">
                    <span class="feedback-icon">⚠</span>
                    Missing path or type
                </div>""",
                status_code=200,
            )

        path = str(path)
        type = str(type)
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

    # Expand paths to absolute (handles ~, relative paths, etc.)
    idea_path_abs = Path(idea_path).expanduser().resolve()
    writings_dir_abs = Path(writings_dir).expanduser().resolve()

    # Validate paths exist before starting workflow
    if not idea_path_abs.exists():
        return HTMLResponse(f'<div class="error">Idea file not found: {idea_path_abs}</div>', status_code=400)
    if not idea_path_abs.is_file():
        return HTMLResponse(f'<div class="error">Idea path is not a file: {idea_path_abs}</div>', status_code=400)
    if not writings_dir_abs.exists():
        return HTMLResponse(
            f'<div class="error">Writings directory not found: {writings_dir_abs}</div>', status_code=400
        )
    if not writings_dir_abs.is_dir():
        return HTMLResponse(
            f'<div class="error">Writings path is not a directory: {writings_dir_abs}</div>', status_code=400
        )

    session_mgr.state.idea_path = str(idea_path_abs)
    session_mgr.state.writings_dir = str(writings_dir_abs)

    # Transfer API key from HTTP session to SessionManager state
    # (Core stages read from environment, which will be set from session state)
    from .configuration import get_api_key

    api_key = get_api_key(request)
    if api_key:
        session_mgr.state.api_key = api_key

    if instructions:
        session_mgr.state.additional_instructions = instructions
    session_mgr.save()

    # Redirect to progress page
    return RedirectResponse(f"/sessions/{session_id}/progress", status_code=303)
