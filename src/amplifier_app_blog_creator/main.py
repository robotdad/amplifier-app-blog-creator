"""Blog Creator CLI - Main entry point."""

import asyncio
import logging
import sys
from pathlib import Path

import click
from amplifier_module_markdown_utils import MarkdownImageUpdater
from amplifier_module_markdown_utils import extract_title
from amplifier_module_markdown_utils import slugify
from amplifier_module_style_extraction import StyleExtractor

from .content_phase import ContentPhase
from .illustration_phase import IllustrationPhase
from .session import SessionManager as StateManager

logger = logging.getLogger(__name__)


@click.command()
@click.option(
    "--idea",
    type=click.Path(exists=True, path_type=Path),
    required=True,
    help="Path to idea/brain dump markdown file",
)
@click.option(
    "--writings-dir",
    type=click.Path(exists=True, file_okay=False, path_type=Path),
    required=True,
    help="Directory containing author's writings for style extraction",
)
@click.option(
    "--instructions",
    type=str,
    default=None,
    help="Additional instructions/context to guide the writing",
)
@click.option(
    "--output",
    type=click.Path(path_type=Path),
    default=None,
    help="Output path for final blog post (default: auto-generated from title)",
)
@click.option(
    "--with-images",
    is_flag=True,
    help="Generate illustrations for the blog post",
)
@click.option(
    "--max-images",
    type=int,
    default=3,
    help="Maximum images to generate (default: 3)",
)
@click.option(
    "--image-style",
    type=str,
    default=None,
    help="Style description for images",
)
@click.option(
    "--resume",
    is_flag=True,
    help="Resume from saved state",
)
@click.option(
    "--reset",
    is_flag=True,
    help="Reset state and start fresh",
)
@click.option(
    "--max-iterations",
    type=int,
    default=10,
    help="Maximum iterations for content (default: 10)",
)
@click.option(
    "--verbose",
    is_flag=True,
    help="Enable verbose logging",
)
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
    """Blog Creator - Transform ideas into polished blog posts with illustrations.

    Example:
        amplifier-app-blog-creator --idea ideas.md --writings-dir my_posts/
    """
    # Setup logging
    if verbose:
        logger.logger.setLevel("DEBUG")

    # Determine session directory
    session_dir = None
    if resume:
        base_dir = Path(".data/blog_creator")
        if base_dir.exists():
            sessions = sorted([d for d in base_dir.iterdir() if d.is_dir()], reverse=True)
            if sessions:
                session_dir = sessions[0]
                logger.info(f"Resuming session: {session_dir.name}")

    # Create state manager
    state_manager = StateManager(session_dir)

    # Handle reset
    if reset:
        state_manager.reset()
        logger.info("State reset - starting fresh")

    # Set max iterations
    state_manager.state.max_iterations = max_iterations

    # Update state with inputs
    state_manager.state.brain_dump_path = str(idea)
    state_manager.state.writings_dir = str(writings_dir)
    if output:
        state_manager.state.output_path = str(output)
    if instructions:
        state_manager.state.additional_instructions = instructions
    state_manager.save()

    logger.info("🚀 Starting Blog Creator Pipeline")
    logger.info(f"  Session: {state_manager.session_dir}")
    logger.info(f"  Idea: {idea.name}")
    logger.info(f"  Writings dir: {writings_dir}")
    if instructions:
        logger.info(f"  Instructions: {instructions}")
    logger.info(f"  Max iterations: {max_iterations}")
    if with_images:
        logger.info(f"  Images: {max_images} (style: {image_style or 'default'})")

    success = asyncio.run(
        run_pipeline(
            idea=idea,
            writings_dir=writings_dir,
            output=output,
            instructions=instructions,
            with_images=with_images,
            max_images=max_images,
            image_style=image_style,
            state_manager=state_manager,
        )
    )

    if success:
        logger.info("\n✨ Blog creation complete!")
        if state_manager.state.output_path:
            logger.info(f"📄 Blog saved to: {state_manager.state.output_path}")
        return 0

    logger.error("\n❌ Blog creation failed")
    return 1


async def run_pipeline(
    idea: Path,
    writings_dir: Path,
    output: Path | None,
    instructions: str | None,
    with_images: bool,
    max_images: int,
    image_style: str | None,
    state_manager: StateManager,
) -> bool:
    """Run the complete blog creation pipeline.

    Args:
        idea: Path to idea file
        writings_dir: Directory with author's writings
        output: Optional output path
        instructions: Optional instructions
        with_images: Whether to generate images
        max_images: Maximum images to generate
        image_style: Image style description
        state_manager: State manager instance

    Returns:
        True if successful
    """
    try:
        # Load brain dump
        brain_dump = idea.read_text()
        logger.info(f"Loaded idea: {idea.name}")

        # Phase 1: Extract style if needed
        if state_manager.state.stage == "initialized":
            logger.info("\n📝 Extracting author's style...")
            state_manager.update_stage("extracting_style")

            style_extractor = StyleExtractor()
            style_profile = await style_extractor.extract_style(writings_dir)

            state_manager.set_style_profile(style_profile.model_dump())
            state_manager.update_stage("style_extracted")

        # Phase 2: Content creation
        content_phase = ContentPhase(state_manager)
        success = await content_phase.run(
            brain_dump=brain_dump,
            brain_dump_path=idea,
            style_profile=state_manager.state.style_profile,
            additional_instructions=instructions,
        )

        if not success:
            return False

        # Save final output
        title = extract_title(state_manager.state.current_draft)
        if title:
            slug = slugify(title)
            output_path = state_manager.session_dir / f"{slug}.md"
        else:
            output_path = output or state_manager.session_dir / "blog_post.md"

        output_path.write_text(state_manager.state.current_draft)
        state_manager.state.output_path = str(output_path)
        state_manager.save()

        logger.info(f"\n💾 Blog post saved to: {output_path}")

        # Phase 3: Illustration (optional)
        if with_images:
            logger.info("\n🎨 Generating illustrations...")
            illustration_phase = IllustrationPhase()

            images_dir = state_manager.session_dir / "images"
            images_dir.mkdir(exist_ok=True)

            generated_images = await illustration_phase.run(
                article_path=output_path,
                output_dir=images_dir,
                style=image_style,
                max_images=max_images,
            )

            if generated_images:
                logger.info(f"✅ Generated {len(generated_images)} images in {images_dir}")

                # Insert images into markdown
                logger.info("📝 Inserting images into blog post...")
                updater = MarkdownImageUpdater()
                content = output_path.read_text()

                # Insert each image
                for i, image_path in enumerate(generated_images, 1):
                    # Make path relative to markdown file
                    relative_path = f"./images/{image_path.name}"
                    alt_text = f"Illustration {i}"

                    # Insert at appropriate position (simple: evenly distributed)
                    # TODO: Could be smarter about placement based on content
                    content = updater.insert_image(
                        content=content,
                        image_path=relative_path,
                        alt_text=alt_text,
                        placement="at_line",
                        line_number=None,  # Will place strategically
                    )

                # Save illustrated version
                illustrated_path = state_manager.session_dir / f"illustrated_{output_path.name}"
                illustrated_path.write_text(content)
                state_manager.state.illustrated_output_path = str(illustrated_path)
                state_manager.save()

                logger.info(f"✅ Illustrated blog post saved to: {illustrated_path}")

        state_manager.mark_complete()
        return True

    except Exception as e:
        logger.error(f"Pipeline failed: {e}")
        return False


if __name__ == "__main__":
    sys.exit(main())
