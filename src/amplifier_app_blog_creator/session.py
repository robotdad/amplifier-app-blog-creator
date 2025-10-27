"""Session Management Module

Handles persistent state for the blog creation workflow, enabling
resume capability across interruptions. Saves state after every
expensive operation.

Consolidates session management from blog_writer and article_illustrator
into a unified session model supporting both content and illustration phases.
"""

import logging
import re
from dataclasses import asdict
from dataclasses import dataclass
from dataclasses import field
from datetime import datetime
from pathlib import Path
from typing import Any

from .vendored_toolkit import read_json
from .vendored_toolkit import safe_write_text
from .vendored_toolkit import write_json

logger = logging.getLogger(__name__)


def extract_title_from_markdown(content: str) -> str | None:
    """Extract the first H1 heading from markdown content.

    Args:
        content: Markdown content

    Returns:
        Title string or None if no title found
    """
    lines = content.strip().split("\n")
    for line in lines:
        line = line.strip()
        if line.startswith("# "):
            return line[2:].strip()
    return None


def slugify(text: str) -> str:
    """Convert text to a URL-friendly slug.

    Args:
        text: Text to slugify

    Returns:
        Slugified string (lowercase, dashes for spaces, no special chars)
    """
    slug = text.lower()
    slug = re.sub(r"[\s_]+", "-", slug)
    slug = re.sub(r"[^a-z0-9-]", "", slug)
    slug = re.sub(r"-+", "-", slug)
    slug = slug.strip("-")
    return slug


@dataclass
class SessionState:
    """Complete session state for blog creation workflow.

    Supports both content creation (Phase 1) and illustration (Phase 2).
    """

    session_id: str
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())
    updated_at: str = field(default_factory=lambda: datetime.now().isoformat())

    # Input parameters
    idea_path: str | None = None
    writings_dir: str | None = None
    output_path: str | None = None
    additional_instructions: str | None = None
    api_key: str | None = None  # For web mode (transferred from HTTP session)

    # Phase 1: Content creation
    stage: str = "initialized"
    iteration: int = 0
    max_iterations: int = 10
    style_profile: dict[str, Any] = field(default_factory=dict)
    current_draft: str = ""
    source_review: dict[str, Any] = field(default_factory=dict)
    style_review: dict[str, Any] = field(default_factory=dict)
    user_feedback: list[dict[str, Any]] = field(default_factory=list)
    iteration_history: list[dict[str, Any]] = field(default_factory=list)

    # Phase 2: Illustration
    illustration_enabled: bool = False
    illustration_points: list[dict[str, Any]] = field(default_factory=list)
    prompts: list[dict[str, Any]] = field(default_factory=list)
    images: list[dict[str, Any]] = field(default_factory=list)
    total_cost: float = 0.0
    analysis_complete: bool = False
    prompts_complete: bool = False
    images_complete: bool = False
    markdown_complete: bool = False
    images_generated: int = 0
    errors: list[dict[str, str]] = field(default_factory=list)

    # Style parameters for illustration
    style_params: dict[str, Any] = field(default_factory=dict)


class SessionManager:
    """Manages session state with automatic persistence.

    Handles both content creation and illustration phases, providing
    checkpoint capability after each expensive operation.
    """

    def __init__(self, session_dir: Path | None = None):
        """Initialize state manager.

        Args:
            session_dir: Path to session directory (default: .data/blog_creator/<timestamp>/)
        """
        if session_dir is None:
            base_dir = Path(".data/blog_creator").expanduser()
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            session_dir = base_dir / timestamp

        self.session_dir = Path(session_dir).expanduser()
        self.session_dir.mkdir(parents=True, exist_ok=True)
        self.state_file = self.session_dir / "state.json"
        self.state = self._load_state()

        # Save initial state if this is a new session
        if not self.state_file.exists():
            self.save()

    def _load_state(self) -> SessionState:
        """Load state from file or create new."""
        if self.state_file.exists():
            try:
                data = read_json(self.state_file)
                logger.info(f"Resumed state from: {self.state_file}")
                logger.info(f"  Stage: {data.get('stage', 'unknown')}")
                logger.info(f"  Iteration: {data.get('iteration', 0)}")
                return SessionState(**data)
            except Exception as e:
                logger.warning(f"Could not load state: {e}")
                logger.info("Starting fresh session")

        return SessionState(session_id=datetime.now().strftime("%Y%m%d_%H%M%S"))

    def save(self) -> None:
        """Save current state to file."""
        self.state.updated_at = datetime.now().isoformat()

        try:
            state_dict = asdict(self.state)
            write_json(state_dict, self.state_file)
            logger.debug(f"State saved to: {self.state_file}")
        except Exception as e:
            logger.error(f"Failed to save state: {e}")

    def update_stage(self, stage: str) -> None:
        """Update workflow stage and save."""
        old_stage = self.state.stage
        self.state.stage = stage
        logger.info(f"Stage: {old_stage} → {stage}")
        self.save()

    def increment_iteration(self) -> bool:
        """Increment iteration counter.

        Returns:
            True if within max iterations, False if exceeded
        """
        self.state.iteration += 1
        logger.info(f"Iteration {self.state.iteration}/{self.state.max_iterations}")

        # Check for max_iterations being None or exceeded
        if self.state.max_iterations is not None and self.state.iteration > self.state.max_iterations:
            logger.warning(f"Exceeded max iterations ({self.state.max_iterations})")
            return False

        self.save()
        return True

    def add_iteration_history(self, entry: dict[str, Any]) -> None:
        """Add entry to iteration history for debugging."""
        entry["iteration"] = self.state.iteration
        entry["timestamp"] = datetime.now().isoformat()
        self.state.iteration_history.append(entry)
        self.save()

    def set_style_profile(self, profile: dict[str, Any]) -> None:
        """Save extracted style profile."""
        self.state.style_profile = profile
        self.save()

    def update_draft(self, draft: str) -> None:
        """Update current draft and save to separate file."""
        self.state.current_draft = draft
        draft_file = self.session_dir / f"draft_iter_{self.state.iteration}.md"
        try:
            safe_write_text(draft, draft_file)
            logger.info(f"Draft saved to: {draft_file}")
        except Exception as e:
            logger.warning(f"Could not save draft file: {e}")
        self.save()

    def set_source_review(self, review: dict[str, Any]) -> None:
        """Save source review results."""
        self.state.source_review = review
        self.save()

    def set_style_review(self, review: dict[str, Any]) -> None:
        """Save style review results."""
        self.state.style_review = review
        self.save()

    def add_user_feedback(self, feedback: dict[str, Any]) -> None:
        """Add user feedback to history."""
        feedback["iteration"] = self.state.iteration
        self.state.user_feedback.append(feedback)
        self.save()

    def add_error(self, stage: str, error: str) -> None:
        """Add an error to the session and save."""
        self.state.errors.append({"stage": stage, "error": str(error)})
        self.save()
        logger.error(f"Error in {stage}: {error}")

    def mark_stage_complete(self, stage: str) -> None:
        """Mark a specific illustration stage as complete."""
        if stage == "analysis":
            self.state.analysis_complete = True
        elif stage == "prompts":
            self.state.prompts_complete = True
        elif stage == "images":
            self.state.images_complete = True
        elif stage == "markdown":
            self.state.markdown_complete = True

        self.save()
        logger.info(f"✅ Stage complete: {stage}")

    def is_complete(self) -> bool:
        """Check if workflow is complete."""
        return self.state.stage == "complete"

    def mark_complete(self) -> None:
        """Mark workflow as complete."""
        self.update_stage("complete")
        logger.info("✅ Workflow complete!")

    def log_progress(self) -> None:
        """Log current progress status."""
        logger.info("Session progress:")
        logger.info(f"  Content stage: {self.state.stage}")
        logger.info(f"  Iteration: {self.state.iteration}/{self.state.max_iterations}")
        if self.state.illustration_enabled:
            logger.info(f"  Analysis: {'✓' if self.state.analysis_complete else '✗'}")
            logger.info(f"  Prompts: {'✓' if self.state.prompts_complete else '✗'}")
            logger.info(
                f"  Images: {'✓' if self.state.images_complete else '✗'} ({self.state.images_generated} generated)"
            )
            logger.info(f"  Markdown: {'✓' if self.state.markdown_complete else '✗'}")
            logger.info(f"  Total cost: ${self.state.total_cost:.2f}")

    def reset(self) -> None:
        """Reset state for fresh run."""
        self.state = SessionState(session_id=datetime.now().strftime("%Y%m%d_%H%M%S"))
        self.save()
        logger.info("State reset for fresh session")
