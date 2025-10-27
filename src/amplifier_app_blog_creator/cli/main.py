"""CLI entry point for blog creator."""

import asyncio
import logging
from pathlib import Path

import click
from amplifier_module_markdown_utils import extract_title
from amplifier_module_markdown_utils import slugify

from ..core.workflow import BlogCreatorWorkflow
from ..illustration_phase import IllustrationPhase
from ..session import SessionManager
from ..vendored_toolkit import safe_write_text
from .input_handler import CLIInputHandler
from .ui import CLIDisplay

logging.basicConfig(level=logging.INFO, format="%(message)s", force=True)
logger = logging.getLogger(__name__)


@click.command()
@click.option("--idea", type=click.Path(exists=True, path_type=Path), required=True, help="Path to idea/brain dump file")
@click.option(
    "--writings-dir",
    type=click.Path(exists=True, file_okay=False, path_type=Path),
    required=True,
    help="Directory with writing samples",
)
@click.option("--instructions", type=str, default=None, help="Additional instructions")
@click.option("--output", type=click.Path(path_type=Path), default=None, help="Output path")
@click.option("--with-images", is_flag=True, help="Generate illustrations")
@click.option("--max-images", type=int, default=3, help="Maximum images (default: 3)")
@click.option("--image-style", type=str, default=None, help="Image style description")
@click.option("--resume", is_flag=True, help="Resume from saved session")
@click.option("--reset", is_flag=True, help="Reset state and start fresh")
@click.option("--max-iterations", type=int, default=10, help="Max iterations (default: 10)")
@click.option("--verbose", is_flag=True, help="Enable verbose logging")
def main(
    idea: Path,
    writings_dir: Path,
    instructions: str | None,
    output: Path | None,
    with_images: bool,
    max_images: int,
    image_style: str | None,
    resume: bool,
    reset: bool,
    max_iterations: int,
    verbose: bool,
):
    """Blog Creator - Transform ideas into polished blog posts."""
    if verbose:
        logging.getLogger().setLevel(logging.DEBUG)

    # Setup session
    session_dir = None
    if resume:
        base_dir = Path(".data/blog_creator")
        if base_dir.exists():
            sessions = sorted([d for d in base_dir.iterdir() if d.is_dir()], reverse=True)
            if sessions:
                session_dir = sessions[0]
                print(f"Resuming session: {session_dir.name}")

    session = SessionManager(session_dir)

    if reset:
        session.reset()
        print("State reset - starting fresh")

    session.state.max_iterations = max_iterations

    # Setup UI
    display = CLIDisplay()
    input_handler = CLIInputHandler(session.session_dir)

    # Create workflow
    workflow = BlogCreatorWorkflow(session, progress_callback=display.show_progress)

    # Run workflow
    success = asyncio.run(
        run_cli_workflow(workflow, display, input_handler, idea, writings_dir, instructions, output, with_images, max_images, image_style)
    )

    return 0 if success else 1


async def run_cli_workflow(
    workflow: BlogCreatorWorkflow,
    display: CLIDisplay,
    input_handler: CLIInputHandler,
    idea: Path,
    writings_dir: Path,
    instructions: str | None,
    output: Path | None,
    with_images: bool,
    max_images: int,
    image_style: str | None,
) -> bool:
    """Run the CLI workflow.

    Args:
        workflow: Workflow orchestrator
        display: CLI display
        input_handler: CLI input handler
        idea: Path to idea file
        writings_dir: Directory with writings
        instructions: Optional instructions
        output: Optional output path
        with_images: Whether to generate images
        max_images: Maximum images
        image_style: Image style description

    Returns:
        True if successful
    """
    try:
        # Show banner
        display.show_banner(str(workflow.session.session_dir), idea.name, str(writings_dir), instructions)

        brain_dump = idea.read_text()

        # Stage 1: Style Extraction
        if workflow.session.state.stage == "initialized":
            display.show_stage("Style Extraction")
            await workflow.run_style_extraction(writings_dir)

        # Stage 2: Initial Draft
        if workflow.session.state.stage == "style_extracted":
            display.show_stage("Draft Generation")
            await workflow.run_draft_generation(brain_dump, instructions)

        # Stage 3-4: Review & Revision Loop
        while workflow.session.state.stage in ["draft_written", "revision_complete"]:
            if not workflow.session.increment_iteration():
                display.show_error("Maximum iterations reached")
                break

            display.show_stage(f"Iteration {workflow.session.state.iteration}")

            # Review
            review = await workflow.run_review()
            display.show_review(review)

            # Get user feedback
            feedback = await input_handler.get_feedback(
                workflow.session.state.current_draft, workflow.session.state.iteration, review.source_issues, review.style_issues
            )

            if feedback.is_approved:
                display.show_success("Draft approved!")
                break

            if not feedback.has_feedback:
                # User skipped - continue if review found issues
                if review.needs_revision:
                    # Auto-revise based on review issues only
                    await workflow.run_revision(feedback)
                continue

            # Apply user feedback
            await workflow.run_revision(feedback)

        # Save final output
        title = extract_title(workflow.session.state.current_draft)
        if title:
            slug = slugify(title)
            output_path = workflow.session.session_dir / f"{slug}.md"
        else:
            output_path = output or workflow.session.session_dir / "blog_post.md"

        safe_write_text(workflow.session.state.current_draft, output_path)
        workflow.session.state.output_path = str(output_path)
        workflow.session.save()

        # Stage 5: Illustration (Optional)
        illustrated_path = None
        if with_images:
            display.show_stage("Illustration")
            illustration_phase = IllustrationPhase()
            images_dir = workflow.session.session_dir / "images"
            images_dir.mkdir(exist_ok=True)

            illustrated_path = await illustration_phase.run(
                article_path=output_path, output_dir=images_dir, style=image_style, max_images=max_images
            )

            if illustrated_path != output_path:
                workflow.session.state.illustrated_output_path = str(illustrated_path)
                workflow.session.save()

        # Completion
        workflow.session.mark_complete()
        display.show_completion(
            str(output_path), str(workflow.session.session_dir), illustrated=with_images, illustrated_path=str(illustrated_path) if illustrated_path else None
        )

        return True

    except Exception as e:
        display.show_error(f"Pipeline failed: {e}")
        logger.exception("Pipeline error details")
        return False


if __name__ == "__main__":
    import sys

    sys.exit(main())
