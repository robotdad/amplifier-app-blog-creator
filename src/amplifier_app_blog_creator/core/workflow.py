"""Workflow orchestrator for blog creation stages."""

import logging
from collections.abc import Callable
from pathlib import Path

from ..session import SessionManager
from .models import ReviewResult
from .models import RevisionFeedback
from .models import StyleProfile
from .stages.draft_generation import generate_draft
from .stages.review import review_draft
from .stages.revision import revise_draft
from .stages.style_extraction import extract_style

logger = logging.getLogger(__name__)


class BlogCreatorWorkflow:
    """Orchestrates blog creation stages with session management."""

    def __init__(
        self: "BlogCreatorWorkflow",
        session_manager: SessionManager,
        progress_callback: Callable[[str], None] | None = None,
    ):
        """Initialize workflow.

        Args:
            session_manager: Session state manager
            progress_callback: Optional callback for progress updates
        """
        self.session = session_manager
        self.progress_callback = progress_callback
        self.brain_dump: str = ""
        self.additional_instructions: str | None = None

    async def run_style_extraction(self: "BlogCreatorWorkflow", writings_dir: Path) -> StyleProfile:
        """Stage 1: Extract writing style from samples.

        Args:
            writings_dir: Directory with writing samples

        Returns:
            Extracted style profile
        """
        self._log("Stage 1: Style Extraction")

        profile = await extract_style(writings_dir, progress_callback=self.progress_callback)

        # Save to session
        self.session.set_style_profile(profile.model_dump())
        self.session.update_stage("style_extracted")

        return profile

    async def run_draft_generation(
        self: "BlogCreatorWorkflow", brain_dump: str, additional_instructions: str | None = None
    ) -> str:
        """Stage 2: Generate initial draft.

        Args:
            brain_dump: User's idea content
            additional_instructions: Optional guidance

        Returns:
            Generated draft
        """
        self._log("Stage 2: Draft Generation")

        # Store for later stages
        self.brain_dump = brain_dump
        self.additional_instructions = additional_instructions

        style_profile = StyleProfile(**self.session.state.style_profile)

        draft = await generate_draft(
            brain_dump,
            style_profile,
            additional_instructions=additional_instructions,
            progress_callback=self.progress_callback,
        )

        # Save to session
        self.session.update_draft(draft)
        self.session.update_stage("draft_written")

        return draft

    async def run_review(self: "BlogCreatorWorkflow") -> ReviewResult:
        """Stage 3: Review current draft.

        Returns:
            Review results with issues
        """
        self._log("Stage 3: Review")

        style_profile = StyleProfile(**self.session.state.style_profile)

        result = await review_draft(
            self.session.state.current_draft,
            self.brain_dump,
            style_profile,
            additional_instructions=self.additional_instructions,
            user_feedback_history=self.session.state.user_feedback,
            progress_callback=self.progress_callback,
        )

        # Save to session
        self.session.set_source_review(result.source_review)
        self.session.set_style_review(result.style_review)

        return result

    async def run_revision(self: "BlogCreatorWorkflow", feedback: RevisionFeedback) -> str:
        """Stage 4: Revise based on feedback.

        Args:
            feedback: Revision feedback and issues

        Returns:
            Revised draft
        """
        self._log("Stage 4: Revision")

        style_profile = StyleProfile(**self.session.state.style_profile)

        revised = await revise_draft(
            self.session.state.current_draft,
            self.brain_dump,
            style_profile,
            feedback,
            additional_instructions=self.additional_instructions,
            progress_callback=self.progress_callback,
        )

        # Save to session
        self.session.update_draft(revised)
        self.session.update_stage("revision_complete")

        return revised

    def _log(self: "BlogCreatorWorkflow", message: str):
        """Internal logging helper."""
        logger.info(message)
        if self.progress_callback:
            self.progress_callback(message)
