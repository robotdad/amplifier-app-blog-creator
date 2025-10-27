"""Content and markdown editing routes."""

import logging
from pathlib import Path
from typing import Annotated

import markdown
from fastapi import APIRouter
from fastapi import Body
from fastapi import Form
from fastapi import Request
from fastapi.responses import HTMLResponse
from fastapi.responses import JSONResponse

from ...session import SessionManager
from ..templates_config import templates

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/sessions")


@router.get("/{session_id}/review", response_class=HTMLResponse)
async def review_page(request: Request, session_id: str):
    """Show review/editor page."""
    session_mgr = SessionManager(Path(f".data/blog_creator/{session_id}"))

    return templates.TemplateResponse(
        "review.html",
        {
            "request": request,
            "session_id": session_id,
            "draft": session_mgr.state.current_draft or "",
            "iteration": session_mgr.state.iteration,
        },
    )


@router.get("/{session_id}/draft")
async def get_draft(session_id: str):
    """Get current draft content."""
    session_mgr = SessionManager(Path(f".data/blog_creator/{session_id}"))
    return JSONResponse({"content": session_mgr.state.current_draft or ""})


@router.put("/{session_id}/draft")
async def update_draft(session_id: str, content: Annotated[str, Body(embed=True)]):
    """Update draft content (auto-save)."""
    session_mgr = SessionManager(Path(f".data/blog_creator/{session_id}"))
    session_mgr.update_draft(content)
    return JSONResponse({"saved": True})


@router.post("/render-markdown")
async def render_markdown(content: Annotated[str, Form()]):
    """Render markdown to HTML for preview."""
    html = markdown.markdown(
        content,
        extensions=[
            "extra",
            "codehilite",
            "sane_lists",
        ],
    )
    return HTMLResponse(f'<div class="markdown-preview">{html}</div>')


@router.get("/{session_id}/review-data")
async def get_review_data(session_id: str):
    """Get review issues for drawer."""
    session_mgr = SessionManager(Path(f".data/blog_creator/{session_id}"))

    source_issues = session_mgr.state.source_review or []
    style_issues = session_mgr.state.style_review or []

    return JSONResponse(
        {
            "source_issues": source_issues,
            "style_issues": style_issues,
            "iteration": session_mgr.state.iteration,
        }
    )


@router.post("/{session_id}/approve")
async def approve_draft(session_id: str):
    """Approve and finalize draft."""
    session_mgr = SessionManager(Path(f".data/blog_creator/{session_id}"))

    # Save final draft
    output_path = session_mgr.session_dir / "output.md"
    output_path.write_text(session_mgr.state.current_draft or "")

    session_mgr.update_stage("complete")

    return JSONResponse({"download_path": str(output_path), "redirect": f"/sessions/{session_id}/complete"})


@router.get("/{session_id}/complete", response_class=HTMLResponse)
async def complete_page(request: Request, session_id: str):
    """Show completion page."""
    session_mgr = SessionManager(Path(f".data/blog_creator/{session_id}"))

    # Calculate word count
    draft = session_mgr.state.current_draft or ""
    word_count = len(draft.split())

    output_path = session_mgr.session_dir / "output.md"

    return templates.TemplateResponse(
        "complete.html",
        {
            "request": request,
            "session_id": session_id,
            "iteration": session_mgr.state.iteration,
            "word_count": word_count,
            "output_path": str(output_path),
        },
    )


@router.get("/{session_id}/download")
async def download_draft(session_id: str):
    """Download final draft as markdown file."""
    from fastapi.responses import FileResponse

    session_mgr = SessionManager(Path(f".data/blog_creator/{session_id}"))
    output_path = session_mgr.session_dir / "output.md"

    if not output_path.exists():
        output_path.write_text(session_mgr.state.current_draft or "")

    return FileResponse(
        path=str(output_path),
        media_type="text/markdown",
        filename=f"blog_post_{session_id[:8]}.md",
    )
