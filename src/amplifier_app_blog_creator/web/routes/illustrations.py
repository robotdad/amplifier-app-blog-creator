"""Illustration generation routes with SSE progress."""

import asyncio
import json
import logging
from pathlib import Path

from fastapi import APIRouter
from fastapi import Request
from fastapi.responses import FileResponse
from fastapi.responses import HTMLResponse
from fastapi.responses import JSONResponse
from sse_starlette.sse import EventSourceResponse

from ...session import SessionManager
from ..templates_config import templates

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/sessions")


class IllustrationQueue:
    """Message queue for illustration progress updates."""

    def __init__(self):
        self.queue: asyncio.Queue = asyncio.Queue()
        self.complete = False

    async def put(
        self,
        message: str,
        stage: str | None = None,
        progress: int | None = None,
        image_path: str | None = None,
    ):
        """Add message to queue with optional stage and progress."""
        data: dict[str, str | int] = {"message": message}
        if stage is not None:
            data["stage"] = stage
        if progress is not None:
            data["progress"] = progress
        if image_path is not None:
            data["image_path"] = image_path
        await self.queue.put(data)

    async def get(self) -> dict[str, str | int]:
        """Get next message from queue."""
        return await self.queue.get()

    def mark_complete(self):
        """Mark generation as complete."""
        self.complete = True


# Session ID to queue mapping
illustration_queues: dict[str, IllustrationQueue] = {}


@router.get("/{session_id}/illustrations", response_class=HTMLResponse)
async def illustrations_page(request: Request, session_id: str):
    """Show illustrations page with editor and generation options."""
    session_mgr = SessionManager(Path(f".data/blog_creator/{session_id}"))

    # Get current draft
    draft = session_mgr.state.current_draft or ""

    return templates.TemplateResponse(
        "illustrations.html",
        {
            "request": request,
            "session_id": session_id,
            "draft": draft,
        },
    )


@router.get("/{session_id}/illustrations-stream")
async def illustrations_stream(session_id: str, style: str = "", max_images: int = 3):
    """SSE stream of illustration generation progress."""

    async def event_generator():
        # Get or create queue for this session
        if session_id not in illustration_queues:
            illustration_queues[session_id] = IllustrationQueue()
            # Start generation in background
            asyncio.create_task(run_illustration_generation(session_id, style, max_images))

        queue = illustration_queues[session_id]

        try:
            while True:
                try:
                    # Wait for next message with timeout for keepalive
                    data = await asyncio.wait_for(queue.get(), timeout=15.0)

                    # Check if this is an image-ready event
                    if "image_path" in data:
                        yield {"event": "image-ready", "data": json.dumps(data)}
                    else:
                        yield {"event": "message", "data": json.dumps(data)}

                except TimeoutError:
                    # Send keepalive
                    yield {"event": "ping", "data": ""}

                    # Check if workflow completed during timeout
                    if queue.complete and queue.queue.empty():
                        break

            # Drain any remaining messages
            while not queue.queue.empty():
                try:
                    data = queue.queue.get_nowait()
                    if "image_path" in data:
                        yield {"event": "image-ready", "data": json.dumps(data)}
                    else:
                        yield {"event": "message", "data": json.dumps(data)}
                except asyncio.QueueEmpty:
                    break

            # Send completion event
            yield {"event": "complete", "data": json.dumps({"success": True})}

        finally:
            # Cleanup queue when client disconnects
            if session_id in illustration_queues:
                del illustration_queues[session_id]

    return EventSourceResponse(event_generator())


async def run_illustration_generation(session_id: str, image_style: str, max_images: int):
    """Generate illustrations using IllustrationPhase with detailed progress updates."""
    queue = illustration_queues[session_id]

    try:
        # Load session
        session_mgr = SessionManager(Path(f".data/blog_creator/{session_id}"))

        # Get current draft
        draft = session_mgr.state.current_draft or ""

        # Save draft to temporary file for IllustrationPhase
        temp_draft_path = session_mgr.session_dir / "temp_draft.md"
        temp_draft_path.write_text(draft)

        # Set up API key
        import os

        api_key = session_mgr.state.api_key or os.getenv("ANTHROPIC_API_KEY")
        if api_key:
            os.environ["ANTHROPIC_API_KEY"] = api_key

        # Images output directory
        images_dir = session_mgr.session_dir / "images"
        images_dir.mkdir(exist_ok=True)

        # Count existing images to generate unique names
        existing_images = list(images_dir.glob("illustration-*.png"))
        start_index = len(existing_images)

        # Import and run IllustrationPhase
        try:
            from ...illustration_phase import IllustrationPhase
        except ImportError:
            await queue.put("Illustration module not available", progress=100)
            logger.warning("IllustrationPhase not found")
            return

        # Create phase instance
        phase = IllustrationPhase()

        # Stage 1: Analyze content
        await queue.put("Analyzing content structure...", stage="analyze")
        await queue.put("Reading markdown sections...", stage="analyze")
        points = await phase._analyze_content(temp_draft_path, max_images)

        if not points:
            await queue.put("No illustration points identified", stage="analyze")
            return

        point_titles = ", ".join([p.section_title for p in points])
        await queue.put(f"Found {len(points)} sections", stage="analyze")
        await queue.put(f"Selected: {point_titles}", stage="analyze")

        # Stage 2: Generate prompts
        await queue.put("Generating contextual prompts...", stage="prompts")
        prompts = await phase._generate_prompts(points, temp_draft_path, image_style)

        for i, prompt in enumerate(prompts):
            await queue.put(f"Generated prompt {i + 1}/{len(prompts)}", stage="prompts")

        await queue.put(f"All {len(prompts)} prompts ready", stage="prompts")

        # Stage 3: Generate images in parallel
        await queue.put(f"Generating {len(prompts)} images in parallel...", stage="prompts")

        # Track individual image generation
        image_results = {}

        async def generate_one_with_progress(prompt, index):
            try:
                # Use unique filename to preserve historical images
                unique_index = start_index + index
                unique_id = f"illustration-{unique_index + 1}"

                await queue.put(f"Starting: {prompt.point.section_title}", stage=f"image-{index}")

                # Generate with unique filename
                image_path = images_dir / f"{unique_id}.png"
                result = await phase.image_generator.generate(
                    prompt=prompt.full_prompt,
                    output_path=image_path,
                    preferred_api="gptimage",
                )

                if result.success:
                    await queue.put(
                        f"✓ Completed: {prompt.point.section_title}",
                        stage=f"image-{index}",
                        image_path=unique_id,
                    )
                    # Use unique_id instead of prompt.illustration_id
                    return (unique_id, result.local_path)
                await queue.put(f"✗ Failed: {result.error}", stage=f"image-{index}")
                return None

            except Exception as e:
                await queue.put(f"Error: {str(e)}", stage=f"image-{index}")
                return None

        # Generate all images in parallel
        results = await asyncio.gather(*[generate_one_with_progress(p, i) for i, p in enumerate(prompts)])

        # Collect successful images
        for result in results:
            if result:
                ill_id, path = result
                image_results[ill_id] = path

        # Stage 4: Insert into markdown
        if image_results:
            await queue.put(f"Inserting {len(image_results)} images...", stage="insert")

            # Read current draft to insert images
            current_content = draft
            lines = current_content.split("\n")

            # Insert images at appropriate positions (after sections)
            # Work backwards to maintain line numbers
            sorted_points = sorted(enumerate(points), key=lambda x: x[1].line_number, reverse=True)

            inserted_count = 0
            for i, point in sorted_points:
                if i < len(image_results):
                    # Get the Nth generated image
                    image_filename = list(image_results.keys())[i]
                    # Insert image markdown with 50% width
                    image_markdown = f'\n<img src="images/{image_filename}.png" alt="{point.section_title}" style="width: 50%; height: auto; display: block; margin: 1.5rem auto;">\n'

                    # Insert after the line number
                    insert_pos = point.line_number
                    if insert_pos < len(lines):
                        lines.insert(insert_pos + 1, image_markdown)
                        inserted_count += 1
                        await queue.put(f"Inserted at line {insert_pos} ({point.suggested_placement})", stage="insert")

            # Update draft with images
            illustrated_content = "\n".join(lines)
            session_mgr.update_draft(illustrated_content)

            await queue.put(f"✓ Successfully inserted {inserted_count} images", stage="insert")
        else:
            await queue.put("No images generated successfully", stage="insert")

    except Exception as e:
        logger.error(f"Illustration generation error: {e}", exc_info=True)
        await queue.put(f"Error: {str(e)}")

    finally:
        queue.mark_complete()


@router.get("/{session_id}/images")
async def get_images(session_id: str):
    """Get list of all images for this session."""
    session_mgr = SessionManager(Path(f".data/blog_creator/{session_id}"))
    images_dir = session_mgr.session_dir / "images"

    if not images_dir.exists():
        return JSONResponse({"images": []})

    # Get all image files
    image_files = []
    for img_path in sorted(images_dir.glob("*.png")):
        image_files.append(
            {
                "filename": img_path.name,
                "path": f"images/{img_path.name}",
                "size": img_path.stat().st_size,
                "created_at": img_path.stat().st_mtime,
            }
        )

    return JSONResponse({"images": image_files})


@router.get("/{session_id}/images/{filename}")
async def get_image_file(session_id: str, filename: str):
    """Serve individual image file."""
    session_mgr = SessionManager(Path(f".data/blog_creator/{session_id}"))
    image_path = session_mgr.session_dir / "images" / filename

    if not image_path.exists():
        return JSONResponse({"error": "Image not found"}, status_code=404)

    return FileResponse(image_path)


@router.post("/{session_id}/render-markdown")
async def render_markdown(request: Request, session_id: str):
    """Render markdown to HTML with image support."""
    form_data = await request.form()
    content = form_data.get("content", "")

    # Simple markdown to HTML conversion
    # (In production, use a proper markdown library like python-markdown)
    import re

    html = str(content)

    # Convert headers
    html = re.sub(r"^### (.*?)$", r"<h3>\1</h3>", html, flags=re.MULTILINE)
    html = re.sub(r"^## (.*?)$", r"<h2>\1</h2>", html, flags=re.MULTILINE)
    html = re.sub(r"^# (.*?)$", r"<h1>\1</h1>", html, flags=re.MULTILINE)

    # Convert images - update paths to serve from session
    html = re.sub(
        r"!\[(.*?)\]\((images/.*?)\)",
        rf'<img src="/sessions/{session_id}/\2" alt="\1">',
        html,
    )

    # Convert bold
    html = re.sub(r"\*\*(.*?)\*\*", r"<strong>\1</strong>", html)

    # Convert italic
    html = re.sub(r"\*(.*?)\*", r"<em>\1</em>", html)

    # Convert code
    html = re.sub(r"`(.*?)`", r"<code>\1</code>", html)

    # Convert paragraphs
    lines = html.split("\n")
    paragraphs = []
    current_p = []

    for line in lines:
        line = line.strip()
        if line.startswith("<h") or line.startswith("<img"):
            if current_p:
                paragraphs.append("<p>" + " ".join(current_p) + "</p>")
                current_p = []
            paragraphs.append(line)
        elif line:
            current_p.append(line)
        else:
            if current_p:
                paragraphs.append("<p>" + " ".join(current_p) + "</p>")
                current_p = []

    if current_p:
        paragraphs.append("<p>" + " ".join(current_p) + "</p>")

    html = "\n".join(paragraphs)

    return HTMLResponse(html)
