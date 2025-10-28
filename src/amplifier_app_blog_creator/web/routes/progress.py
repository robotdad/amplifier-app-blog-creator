"""Progress streaming routes using SSE."""

import asyncio
import json
import logging
from pathlib import Path

from fastapi import APIRouter
from fastapi import Request
from fastapi.responses import HTMLResponse
from sse_starlette.sse import EventSourceResponse

from ...core.models import RevisionFeedback
from ...core.workflow import BlogCreatorWorkflow
from ...session import SessionManager
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
    """Run blog creation workflow with progress updates."""
    queue = progress_queues[session_id]

    try:
        # Load session
        session_mgr = SessionManager(Path(f".data/blog_creator/{session_id}"))

        # Get API key from session state (stored during configuration)
        # Core stages read from environment, so set it here
        import os

        api_key = session_mgr.state.api_key or os.getenv("ANTHROPIC_API_KEY")

        if not api_key:
            await queue.put("Error: No API key configured")
            return

        os.environ["ANTHROPIC_API_KEY"] = api_key

        # Progress callback
        def progress_callback(message: str):
            asyncio.create_task(queue.put(message))

        await queue.put("Starting workflow...")

        # Get paths from session
        idea_path_str = session_mgr.state.idea_path
        writings_dir_str = session_mgr.state.writings_dir

        if not idea_path_str or not writings_dir_str:
            await queue.put("Error: Missing required paths")
            return

        idea_path = Path(idea_path_str)
        writings_dir = Path(writings_dir_str)

        # Create workflow
        workflow = BlogCreatorWorkflow(session_mgr, progress_callback=progress_callback)

        # Read idea file
        brain_dump = idea_path.read_text()
        additional_instructions = session_mgr.state.additional_instructions

        # Stage 1: Style Extraction
        await queue.put("Extracting writing style...", stage="style_extraction", stage_index=0)
        await workflow.run_style_extraction(writings_dir)

        # Stage 2: Draft Generation
        await queue.put("Generating initial draft...", stage="draft_generation", stage_index=1)
        await workflow.run_draft_generation(brain_dump, additional_instructions)

        # Stage 3: Review (first pass - like CLI iteration 1)
        await queue.put("Reviewing draft...", stage="review", stage_index=2)
        review_result = await workflow.run_review()

        # Stage 4: Auto-revision if issues found (match CLI's first-pass behavior)
        if review_result.needs_revision:
            # Increment iteration before revision (this will be iter_1)
            if not session_mgr.increment_iteration():
                await queue.put("Error: Maximum iterations reached")
                return

            await queue.put("Revising based on review feedback...", stage="revision", stage_index=3)
            feedback = RevisionFeedback(
                action="revise", source_issues=review_result.source_issues, style_issues=review_result.style_issues
            )
            await workflow.run_revision(feedback)

            # Review again after revision
            await queue.put("Final review...", stage="revision", stage_index=3)
            await workflow.run_review()

        await queue.put("Workflow complete!", stage="complete", stage_index=4)

    except Exception as e:
        logger.error(f"Workflow error: {e}", exc_info=True)
        await queue.put(f"Error: {str(e)}")

    finally:
        queue.mark_complete()
