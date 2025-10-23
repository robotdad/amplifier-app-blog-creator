"""Content phase workflow orchestration.

Coordinates blog writing with review and user feedback.
"""

import asyncio
from pathlib import Path

from amplifier.utils.logger import get_logger

from .blog_writer import BlogWriter
from .feedback import UserFeedbackHandler
from .reviewers.source_reviewer import SourceReviewer
from .reviewers.style_reviewer import StyleReviewer
from .session import SessionManager as StateManager

logger = get_logger(__name__)


class ContentPhase:
    """Orchestrates blog content creation with review and feedback."""

    def __init__(self, state: StateManager):
        """Initialize content phase.

        Args:
            state: State manager instance
        """
        self.state = state
        self.blog_writer = BlogWriter()
        self.source_reviewer = SourceReviewer()
        self.style_reviewer = StyleReviewer()
        self.user_feedback = UserFeedbackHandler()

    async def run(
        self,
        brain_dump: str,
        brain_dump_path: Path,
        style_profile: dict,
        additional_instructions: str | None = None,
    ) -> bool:
        """Run the content creation phase.

        Args:
            brain_dump: The idea/brain dump content
            brain_dump_path: Path to brain dump file
            style_profile: Extracted style profile
            additional_instructions: Optional guidance

        Returns:
            True if successful
        """
        logger.info("Starting content creation phase")

        # Store inputs
        self.brain_dump = brain_dump
        self.additional_instructions = additional_instructions or ""

        # Resume from saved stage if applicable
        stage = self.state.state.stage
        logger.info(f"Current stage: {stage}")

        try:
            # Write initial draft
            if stage == "style_extracted":
                await self._write_initial_draft(brain_dump, style_profile, additional_instructions)
                stage = self.state.state.stage

            # Iteration loop
            while stage in ["draft_written", "revision_complete"]:
                if not self.state.increment_iteration():
                    logger.warning("Max iterations reached")
                    break

                # Source review
                await self._review_sources()

                # Style review
                await self._review_style()

                # Check if revision needed
                needs_revision = self.state.state.source_review.get(
                    "needs_revision", False
                ) or self.state.state.style_review.get("needs_revision", False)

                if needs_revision:
                    await self._revise_draft()

                # User feedback
                feedback = await self._get_user_feedback()
                if feedback.get("is_approved"):
                    break

                if feedback.get("continue_iteration"):
                    await self._apply_user_feedback(feedback, increment_after=True)
                else:
                    break

                stage = self.state.state.stage

            return True

        except Exception as e:
            logger.error(f"Content phase failed: {e}")
            return False

    async def _write_initial_draft(
        self, brain_dump: str, style_profile: dict, additional_instructions: str | None
    ) -> None:
        """Write initial blog draft."""
        logger.info("\n✍️ Writing initial blog draft...")
        self.state.update_stage("writing_draft")

        draft = await self.blog_writer.write_blog(
            brain_dump,
            style_profile,
            additional_instructions=additional_instructions,
        )

        logger.debug(f"Generated draft length: {len(draft)} chars")
        self.state.update_draft(draft)
        self.state.update_stage("draft_written")

    async def _review_sources(self) -> None:
        """Review draft for source accuracy."""
        logger.info("\n🔍 Reviewing source accuracy...")

        review = await self.source_reviewer.review_sources(
            self.state.state.current_draft,
            self.brain_dump,
            additional_instructions=self.additional_instructions,
            user_feedback_history=self.state.state.user_feedback,
        )

        self.state.set_source_review(review)
        self.state.add_iteration_history({"type": "source_review", "review": review})

    async def _review_style(self) -> None:
        """Review draft for style consistency."""
        logger.info("\n🎨 Reviewing style consistency...")

        review = await self.style_reviewer.review_style(
            self.state.state.current_draft,
            self.state.state.style_profile,
        )

        self.state.set_style_review(review)
        self.state.add_iteration_history({"type": "style_review", "review": review})

    async def _revise_draft(self) -> None:
        """Revise draft based on reviews."""
        logger.info("\n🔄 Revising draft based on reviews...")

        # Compile feedback from reviews
        feedback = {
            "source_issues": self.state.state.source_review.get("issues", []),
            "style_issues": self.state.state.style_review.get("issues", []),
            "user_requests": [],
        }

        draft = await self.blog_writer.write_blog(
            self.brain_dump,
            self.state.state.style_profile,
            previous_draft=self.state.state.current_draft,
            feedback=feedback,
            additional_instructions=self.additional_instructions,
        )

        self.state.update_draft(draft)
        self.state.update_stage("revision_complete")

    async def _get_user_feedback(self) -> dict:
        """Get user feedback on current draft."""
        logger.info("\n👤 Getting user feedback...")

        draft_file_path = self.state.session_dir / f"draft_iter_{self.state.state.iteration}.md"

        # Run in thread to handle blocking input
        loop = asyncio.get_event_loop()
        feedback = await loop.run_in_executor(
            None,
            self.user_feedback.get_user_feedback,
            self.state.state.current_draft,
            self.state.state.iteration,
            draft_file_path,
        )

        self.state.add_user_feedback(feedback)
        self.state.add_iteration_history({"type": "user_feedback", "feedback": feedback})

        return feedback

    async def _apply_user_feedback(self, parsed_feedback: dict, increment_after: bool = False) -> None:
        """Apply user feedback to draft.

        Args:
            parsed_feedback: The parsed user feedback
            increment_after: If True, increment iteration before saving draft
        """
        if not parsed_feedback.get("has_feedback"):
            return

        logger.info("\n📝 Applying user feedback...")

        # Format feedback for revision
        feedback = self.user_feedback.format_feedback_for_revision(parsed_feedback)

        # Add issues from reviews
        feedback["source_issues"] = self.state.state.source_review.get("issues", [])
        feedback["style_issues"] = self.state.state.style_review.get("issues", [])

        draft = await self.blog_writer.write_blog(
            self.brain_dump,
            self.state.state.style_profile,
            previous_draft=self.state.state.current_draft,
            feedback=feedback,
            additional_instructions=self.additional_instructions,
        )

        # Increment BEFORE saving so we write to next iteration
        if increment_after and not self.state.increment_iteration():
            logger.warning("Max iterations reached while applying user feedback")
            return

        self.state.update_draft(draft)
        self.state.update_stage("revision_complete")
