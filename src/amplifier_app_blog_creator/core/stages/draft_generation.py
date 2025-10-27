"""Draft generation stage - wraps BlogWriter for initial draft."""

from typing import Callable

from ...blog_writer import BlogWriter
from ..models import StyleProfile


async def generate_draft(
    brain_dump: str,
    style_profile: StyleProfile,
    additional_instructions: str | None = None,
    progress_callback: Callable[[str], None] | None = None,
) -> str:
    """Generate initial blog draft.

    Args:
        brain_dump: User's idea/notes
        style_profile: Extracted writing style
        additional_instructions: Optional guidance
        progress_callback: Optional callback for progress

    Returns:
        Draft markdown content
    """
    if progress_callback:
        progress_callback("Generating draft...")

    writer = BlogWriter()
    draft = await writer.write_blog(brain_dump, style_profile.model_dump(), additional_instructions=additional_instructions)

    if progress_callback:
        progress_callback(f"Draft complete ({len(draft)} characters)")

    return draft
