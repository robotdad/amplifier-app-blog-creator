"""CLI input handling - adapts UserFeedbackHandler to core models."""

import asyncio
import logging
from pathlib import Path

from ..core.models import RevisionFeedback
from ..feedback import UserFeedbackHandler

logger = logging.getLogger(__name__)


class CLIInputHandler:
    """Handles user input for CLI."""

    def __init__(self: "CLIInputHandler", session_dir: Path):
        """Initialize handler.

        Args:
            session_dir: Session directory for draft files
        """
        self.session_dir = session_dir
        self.handler = UserFeedbackHandler()

    async def get_feedback(
        self: "CLIInputHandler", current_draft: str, iteration: int, source_issues: list[str], style_issues: list[str]
    ) -> RevisionFeedback:
        """Get user feedback on draft.

        Args:
            current_draft: Current draft content
            iteration: Current iteration number
            source_issues: Issues from source review
            style_issues: Issues from style review

        Returns:
            RevisionFeedback model
        """
        draft_file = self.session_dir / f"draft_iter_{iteration}.md"

        # Get feedback using existing handler (blocking I/O in thread)
        loop = asyncio.get_event_loop()
        parsed = await loop.run_in_executor(None, self.handler.get_user_feedback, current_draft, iteration, draft_file)

        # Convert parsed feedback dict to RevisionFeedback model
        if parsed.get("is_approved"):
            return RevisionFeedback(action="approve", source_issues=source_issues, style_issues=style_issues, user_requests=[])

        if not parsed.get("has_feedback"):
            return RevisionFeedback(action="skip", source_issues=source_issues, style_issues=style_issues, user_requests=[])

        # Has feedback - format it
        formatted = self.handler.format_feedback_for_revision(parsed)
        user_requests = formatted.get("user_requests", [])

        return RevisionFeedback(action="revise", source_issues=source_issues, style_issues=style_issues, user_requests=user_requests)
