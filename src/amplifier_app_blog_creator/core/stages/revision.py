"""Revision stage - wraps BlogWriter for draft revision."""

from collections.abc import Callable

from ...blog_writer import BlogWriter
from ..models import RevisionFeedback
from ..models import StyleProfile


async def revise_draft(
    draft: str,
    brain_dump: str,
    style_profile: StyleProfile,
    feedback: RevisionFeedback,
    additional_instructions: str | None = None,
    progress_callback: Callable[[str], None] | None = None,
) -> str:
    """Revise draft based on feedback.

    Args:
        draft: Current draft
        brain_dump: Original idea
        style_profile: Target style
        feedback: Issues and user requests
        additional_instructions: Optional guidance
        progress_callback: Optional callback for progress

    Returns:
        Revised draft content
    """
    if progress_callback:
        progress_callback("Revising draft...")

    # Convert RevisionFeedback to dict format BlogWriter expects
    feedback_dict = {
        "source_issues": feedback.source_issues,
        "style_issues": feedback.style_issues,
        "user_requests": feedback.user_requests,
    }

    writer = BlogWriter()
    revised = await writer.write_blog(
        brain_dump,
        style_profile.model_dump(),
        previous_draft=draft,
        feedback=feedback_dict,
        additional_instructions=additional_instructions,
    )

    if progress_callback:
        progress_callback(f"Revision complete ({len(revised)} characters)")

    return revised
