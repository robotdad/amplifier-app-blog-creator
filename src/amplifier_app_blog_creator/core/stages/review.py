"""Review stage - combines source and style reviewers."""

from collections.abc import Callable

from ...reviewers.source_reviewer import SourceReviewer
from ...reviewers.style_reviewer import StyleReviewer
from ..models import ReviewResult
from ..models import StyleProfile


async def review_draft(
    draft: str,
    brain_dump: str,
    style_profile: StyleProfile,
    additional_instructions: str | None = None,
    user_feedback_history: list[dict] | None = None,
    progress_callback: Callable[[str], None] | None = None,
) -> ReviewResult:
    """Review draft for accuracy and style.

    Args:
        draft: Current draft content
        brain_dump: Original idea
        style_profile: Target writing style
        additional_instructions: Optional guidance to verify
        user_feedback_history: History of user feedback
        progress_callback: Optional callback for progress

    Returns:
        ReviewResult with issues found
    """
    if progress_callback:
        progress_callback("Reviewing draft for accuracy...")

    source_reviewer = SourceReviewer()
    source_review = await source_reviewer.review_sources(
        draft,
        brain_dump,
        additional_instructions=additional_instructions,
        user_feedback_history=user_feedback_history or [],
    )

    if progress_callback:
        progress_callback("Reviewing draft for style...")

    style_reviewer = StyleReviewer()
    style_review = await style_reviewer.review_style(draft, style_profile.model_dump())

    if progress_callback:
        issues_count = len(source_review.get("issues", [])) + len(style_review.get("issues", []))
        if issues_count > 0:
            progress_callback(f"Review complete ({issues_count} issues found)")
        else:
            progress_callback("Review complete (no issues)")

    return ReviewResult(source_review=source_review, style_review=style_review)
