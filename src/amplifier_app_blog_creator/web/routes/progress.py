"""Progress streaming routes using SSE."""

import asyncio
import json
import logging
from pathlib import Path

from fastapi import APIRouter
from fastapi import Request
from fastapi.responses import HTMLResponse
from sse_starlette.sse import EventSourceResponse

from ...session import SessionManager
from ..recipe_executor import RecipeExecutor
from ..templates_config import templates

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/sessions")


class MessageQueue:
    """Simple message queue for progress updates."""

    def __init__(self):
        self.queue: asyncio.Queue = asyncio.Queue()
        self.complete = False
        self.current_stage: str | None = None
        self.current_stage_index: int = -1

    async def put(self, message: str, stage: str | None = None, stage_index: int | None = None):
        """Add message to queue with optional stage info."""
        data: dict[str, str | int] = {"message": message}
        if stage is not None:
            data["stage"] = stage
            self.current_stage = stage
        if stage_index is not None:
            data["stage_index"] = stage_index
            self.current_stage_index = stage_index
        await self.queue.put(data)

    async def get(self) -> dict[str, str | int]:
        """Get next message from queue."""
        return await self.queue.get()

    def mark_complete(self):
        """Mark workflow as complete."""
        self.complete = True


# Session ID to queue mapping
progress_queues: dict[str, MessageQueue] = {}


@router.get("/{session_id}/progress", response_class=HTMLResponse)
async def progress_page(request: Request, session_id: str):
    """Show progress page."""
    return templates.TemplateResponse(
        "progress.html",
        {
            "request": request,
            "session_id": session_id,
        },
    )


@router.get("/{session_id}/progress-stream")
async def progress_stream(session_id: str):
    """SSE stream of progress updates."""

    async def event_generator():
        # Get or create queue for this session
        if session_id not in progress_queues:
            progress_queues[session_id] = MessageQueue()
            # Start workflow in background
            asyncio.create_task(run_workflow(session_id))

        queue = progress_queues[session_id]

        try:
            while not queue.complete:
                try:
                    # Wait for next message with timeout for keepalive
                    data = await asyncio.wait_for(queue.get(), timeout=15.0)
                    yield {"event": "message", "data": json.dumps(data)}
                except TimeoutError:
                    # Send keepalive
                    yield {"event": "ping", "data": ""}

            # Send completion event
            yield {"event": "complete", "data": json.dumps({"redirect": f"/sessions/{session_id}/review"})}

        finally:
            # Cleanup queue when client disconnects
            if session_id in progress_queues:
                del progress_queues[session_id]

    return EventSourceResponse(event_generator())


async def run_workflow(session_id: str):
    """Run blog creation workflow via recipe execution."""
    queue = progress_queues[session_id]

    try:
        # Load session
        session_mgr = SessionManager(Path(f".data/blog_creator/{session_id}"))

        # Get API key from session state (stored during configuration)
        # Recipe execution reads from environment, so set it here
        import os

        api_key = session_mgr.state.api_key or os.getenv("ANTHROPIC_API_KEY")

        if not api_key:
            await queue.put("Error: No API key configured", stage="error")
            return

        os.environ["ANTHROPIC_API_KEY"] = api_key

        # Read idea file content
        idea_path = Path(session_mgr.state.idea_path)
        topic_content = idea_path.read_text()

        # Build recipe context
        recipe_context = {
            "topic": topic_content,
            "style_samples_dir": session_mgr.state.writings_dir,
            "additional_instructions": session_mgr.state.additional_instructions or "",
            "with_illustrations": "false",  # Not supported in web UI yet
            "max_images": "0",
        }

        # Execute recipe
        recipe_path = Path("amplifier-bundle-blog-creator/recipes/create-blog-post.yaml")
        executor = RecipeExecutor(recipe_path)

        success = await executor.execute(
            context=recipe_context, session_dir=session_mgr.session_dir, queue=queue
        )

        if not success:
            await queue.put("Error: Recipe execution failed", stage="error")

    except Exception as e:
        logger.error(f"Workflow error: {e}", exc_info=True)
        await queue.put(f"Error: {str(e)}", stage="error")

    finally:
        queue.mark_complete()
