"""Core data models for blog creator workflow."""

from typing import Literal

from pydantic import BaseModel
from pydantic import Field


class StyleProfile(BaseModel):
    """Author's writing style profile."""

    tone: str
    voice: str
    vocabulary_level: str
    sentence_structure: str
    paragraph_length: str
    common_phrases: list[str] = Field(default_factory=list)
    writing_patterns: list[str] = Field(default_factory=list)
    examples: list[str] = Field(default_factory=list)


class ReviewResult(BaseModel):
    """Combined review results from source and style reviewers."""

    source_review: dict
    style_review: dict

    @property
    def needs_revision(self: "ReviewResult") -> bool:
        """Check if revision is needed based on reviews."""
        return self.source_review.get("needs_revision", False) or self.style_review.get("needs_revision", False)

    @property
    def source_issues(self: "ReviewResult") -> list[str]:
        """Get source accuracy issues."""
        return self.source_review.get("issues", [])

    @property
    def style_issues(self: "ReviewResult") -> list[str]:
        """Get style consistency issues."""
        return self.style_review.get("issues", [])


class RevisionFeedback(BaseModel):
    """Feedback for draft revision."""

    action: Literal["approve", "revise", "skip"]
    source_issues: list[str] = Field(default_factory=list)
    style_issues: list[str] = Field(default_factory=list)
    user_requests: list[str] = Field(default_factory=list)

    @property
    def is_approved(self: "RevisionFeedback") -> bool:
        """Check if user approved the draft."""
        return self.action == "approve"

    @property
    def has_feedback(self: "RevisionFeedback") -> bool:
        """Check if there is actionable feedback."""
        return bool(self.user_requests) or self.action == "revise"
