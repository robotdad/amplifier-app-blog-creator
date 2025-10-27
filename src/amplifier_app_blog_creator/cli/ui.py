"""CLI display functions - all output to user."""

import logging

from ..core.models import ReviewResult

logger = logging.getLogger(__name__)


class CLIDisplay:
    """Handles all CLI output display."""

    def show_banner(self: "CLIDisplay", session_dir: str, idea_name: str, writings_dir: str, instructions: str | None = None):
        """Show startup banner.

        Args:
            session_dir: Session directory path
            idea_name: Name of idea file
            writings_dir: Writings directory path
            instructions: Optional additional instructions
        """
        print("\n" + "=" * 60)
        print("🚀 BLOG CREATOR")
        print("=" * 60)
        print(f"Session: {session_dir}")
        print(f"Idea: {idea_name}")
        print(f"Writings: {writings_dir}")
        if instructions:
            print(f"Instructions: {instructions}")
        print("=" * 60 + "\n")

    def show_stage(self: "CLIDisplay", stage: str):
        """Show stage transition.

        Args:
            stage: Stage name to display
        """
        print(f"\n{'=' * 60}")
        print(f"📍 {stage}")
        print("=" * 60)

    def show_progress(self: "CLIDisplay", message: str):
        """Show progress message.

        Args:
            message: Progress message to display
        """
        print(f"   {message}")

    def show_review(self: "CLIDisplay", review: ReviewResult):
        """Display review results.

        Args:
            review: Review result to display
        """
        print("\n" + "-" * 60)
        print("📋 REVIEW RESULTS")
        print("-" * 60)

        source_count = len(review.source_issues)
        style_count = len(review.style_issues)

        print(f"Source Accuracy: {source_count} issue(s)")
        if source_count > 0:
            for i, issue in enumerate(review.source_issues, 1):
                print(f"  {i}. {issue}")

        print(f"\nStyle Consistency: {style_count} issue(s)")
        if style_count > 0:
            for i, issue in enumerate(review.style_issues, 1):
                print(f"  {i}. {issue}")

        if review.needs_revision:
            print("\n⚠️  Revision needed")
        else:
            print("\n✅ Draft looks good")

        print("-" * 60)

    def show_success(self: "CLIDisplay", message: str):
        """Show success message.

        Args:
            message: Success message to display
        """
        print(f"\n✨ {message}\n")

    def show_error(self: "CLIDisplay", message: str):
        """Show error message.

        Args:
            message: Error message to display
        """
        print(f"\n❌ {message}\n")
        logger.error(message)

    def show_completion(
        self: "CLIDisplay",
        output_path: str,
        session_dir: str,
        illustrated: bool = False,
        illustrated_path: str | None = None,
    ):
        """Show completion message.

        Args:
            output_path: Path to final blog post
            session_dir: Session directory
            illustrated: Whether illustrations were generated
            illustrated_path: Path to illustrated version if generated
        """
        print("\n" + "=" * 60)
        print("✨ BLOG CREATION COMPLETE")
        print("=" * 60)
        print(f"\n📄 Blog post: {output_path}")

        if illustrated and illustrated_path:
            print(f"🎨 Illustrated version: {illustrated_path}")

        print(f"\n📁 Session directory: {session_dir}")
        print("=" * 60 + "\n")
