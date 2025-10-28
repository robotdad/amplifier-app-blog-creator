"""Content and markdown editing routes."""

import logging
from pathlib import Path
from typing import Annotated

import bleach
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


@router.post("/{session_id}/render-markdown")
async def render_markdown(session_id: str, content: Annotated[str, Form()]):
    """Render markdown to HTML for preview with image support."""
    html = markdown.markdown(
        content,
        extensions=[
            "extra",
            "codehilite",
            "sane_lists",
        ],
    )

    # Rewrite image paths to point to session endpoint
    import re

    html = re.sub(
        r'<img src="images/([^"]+)"',
        rf'<img src="/sessions/{session_id}/images/\1"',
        html,
    )

    # Sanitize HTML to prevent XSS
    safe_html = bleach.clean(
        html,
        tags=[
            "p",
            "br",
            "strong",
            "em",
            "u",
            "h1",
            "h2",
            "h3",
            "h4",
            "h5",
            "h6",
            "ul",
            "ol",
            "li",
            "a",
            "code",
            "pre",
            "blockquote",
            "hr",
            "table",
            "thead",
            "tbody",
            "tr",
            "th",
            "td",
            "img",
        ],
        attributes={
            "a": ["href", "title"],
            "code": ["class"],
            "img": ["src", "alt", "title", "style"],
        },
        strip=True,
    )

    return HTMLResponse(f'<div class="markdown-preview">{safe_html}</div>')


@router.get("/{session_id}/review-data")
async def get_review_data(session_id: str):
    """Get review issues for drawer."""
    session_mgr = SessionManager(Path(f".data/blog_creator/{session_id}"))

    # Extract issues arrays from review dicts
    source_issues = session_mgr.state.source_review.get("issues", []) if session_mgr.state.source_review else []
    style_issues = session_mgr.state.style_review.get("issues", []) if session_mgr.state.style_review else []

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
    from amplifier_module_markdown_utils import extract_title
    from amplifier_module_markdown_utils import slugify

    session_mgr = SessionManager(Path(f".data/blog_creator/{session_id}"))

    # Extract title and create slug like CLI does
    draft = session_mgr.state.current_draft or ""
    title = extract_title(draft)
    slug = slugify(title) if title else "blog-post"

    # Save final draft with slug-based filename
    output_path = session_mgr.session_dir / f"{slug}.md"
    output_path.write_text(draft)

    session_mgr.update_stage("complete")

    return JSONResponse({"download_path": str(output_path), "redirect": f"/sessions/{session_id}/complete"})


@router.get("/{session_id}/complete", response_class=HTMLResponse)
async def complete_page(request: Request, session_id: str):
    """Show completion page with full absolute paths."""
    from amplifier_module_markdown_utils import extract_title
    from amplifier_module_markdown_utils import slugify

    session_mgr = SessionManager(Path(f".data/blog_creator/{session_id}"))

    # Calculate word count
    draft = session_mgr.state.current_draft or ""
    word_count = len(draft.split())

    # Use same slug logic as approve endpoint
    title = extract_title(draft)
    slug = slugify(title) if title else "blog-post"
    draft_filename = f"{slug}.md"

    # Get absolute session path
    session_path = session_mgr.session_dir.resolve()

    # Check for images
    images_dir = session_mgr.session_dir / "images"
    has_images = images_dir.exists() and any(images_dir.glob("*.png"))
    image_files = [img.name for img in sorted(images_dir.glob("*.png"))] if has_images else []

    return templates.TemplateResponse(
        "complete.html",
        {
            "request": request,
            "session_id": session_id,
            "iteration": session_mgr.state.iteration,
            "word_count": word_count,
            "session_path": str(session_path),
            "draft_filename": draft_filename,
            "has_images": has_images,
            "image_files": image_files,
        },
    )


@router.get("/{session_id}/download")
async def download_draft(session_id: str):
    """Download final draft as markdown file."""
    from amplifier_module_markdown_utils import extract_title
    from amplifier_module_markdown_utils import slugify
    from fastapi.responses import FileResponse

    session_mgr = SessionManager(Path(f".data/blog_creator/{session_id}"))

    # Use same slug logic for consistency
    draft = session_mgr.state.current_draft or ""
    title = extract_title(draft)
    slug = slugify(title) if title else "blog-post"
    output_path = session_mgr.session_dir / f"{slug}.md"

    if not output_path.exists():
        output_path.write_text(draft)

    return FileResponse(
        path=str(output_path),
        media_type="text/markdown",
        filename=f"{slug}.md",
        headers={"Content-Disposition": f'attachment; filename="{slug}.md"'},
    )


@router.get("/{session_id}/download-zip")
async def download_zip(session_id: str):
    """Download content and images as ZIP file."""
    import io
    import zipfile

    from amplifier_module_markdown_utils import extract_title
    from amplifier_module_markdown_utils import slugify
    from fastapi.responses import StreamingResponse

    session_mgr = SessionManager(Path(f".data/blog_creator/{session_id}"))

    # Get slug for filename
    draft = session_mgr.state.current_draft or ""
    title = extract_title(draft)
    slug = slugify(title) if title else "blog-post"

    # Create ZIP in memory
    zip_buffer = io.BytesIO()

    with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zip_file:
        # Add markdown file
        zip_file.writestr(f"{slug}.md", draft)

        # Add images if they exist
        images_dir = session_mgr.session_dir / "images"
        if images_dir.exists():
            for img_path in images_dir.glob("*.png"):
                # Add to images/ folder in ZIP
                zip_file.write(img_path, f"images/{img_path.name}")

    zip_buffer.seek(0)

    return StreamingResponse(
        io.BytesIO(zip_buffer.read()),
        media_type="application/zip",
        headers={"Content-Disposition": f'attachment; filename="{slug}.zip"'},
    )


@router.post("/{session_id}/open-folder")
async def open_folder(session_id: str):
    """Open session folder in system file manager."""
    import platform
    import subprocess

    session_mgr = SessionManager(Path(f".data/blog_creator/{session_id}"))
    folder_path = session_mgr.session_dir.resolve()

    try:
        system = platform.system()
        if system == "Darwin":  # macOS
            subprocess.run(["open", str(folder_path)], check=True)
        elif system == "Windows":
            subprocess.run(["explorer", str(folder_path)], check=True)
        else:  # Linux
            subprocess.run(["xdg-open", str(folder_path)], check=True)

        return JSONResponse({"success": True})
    except Exception as e:
        logger.error(f"Failed to open folder: {e}")
        return JSONResponse({"success": False, "error": str(e)}, status_code=500)
