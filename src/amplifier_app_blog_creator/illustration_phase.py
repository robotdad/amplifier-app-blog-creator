"""Illustration Phase - Generate images for blog posts.

Analyzes content, generates image prompts, and creates illustrations.
"""

import logging
from pathlib import Path

from amplifier_module_image_generation import ImageGenerator

logger = logging.getLogger(__name__)


class IllustrationPhase:
    """Orchestrates image generation for blog posts."""

    def __init__(self):
        """Initialize illustration phase."""
        self.image_generator = ImageGenerator()

    async def run(
        self,
        article_path: Path,
        output_dir: Path,
        style: str | None = None,
        max_images: int = 3,
        apis: list[str] | None = None,
    ) -> list[Path]:
        """Generate illustrations for blog post.

        Args:
            article_path: Path to blog markdown
            output_dir: Directory to save images
            style: Optional style description
            max_images: Maximum images to generate
            apis: List of image APIs to try

        Returns:
            List of generated image paths
        """
        logger.info(f"Starting illustration generation (max {max_images} images)")

        if apis is None:
            apis = ["gptimage"]

        # Read article content
        content = article_path.read_text()

        # Simple prompt generation
        prompts = self._generate_prompts(content, style, max_images)

        # Generate images
        generated_images = []
        output_dir.mkdir(parents=True, exist_ok=True)

        for i, prompt in enumerate(prompts, 1):
            logger.info(f"Generating image {i}/{len(prompts)}")

            try:
                # Generate output path for this image
                image_path = output_dir / f"illustration_{i}.png"

                # Use first API from list as preferred
                preferred_api = apis[0] if apis else "gptimage"

                result = await self.image_generator.generate(
                    prompt=prompt, output_path=image_path, preferred_api=preferred_api
                )

                if result.success:
                    generated_images.append(result.local_path)
                    logger.info(f"✓ Generated: {result.local_path.name} (cost: ${result.cost:.4f})")
                else:
                    logger.error(f"Failed to generate image {i}: {result.error}")
            except Exception as e:
                logger.error(f"Failed to generate image {i}: {e}")

        logger.info(f"Generated {len(generated_images)}/{len(prompts)} images")
        return generated_images

    def _generate_prompts(self, content: str, style: str | None, max_images: int) -> list[str]:
        """Generate simple image prompts from content.

        Args:
            content: Article content
            style: Optional style description
            max_images: Maximum prompts to generate

        Returns:
            List of image prompts
        """
        # Simple implementation: extract key sections
        lines = content.split("\n")
        headers = [line for line in lines if line.startswith("#")]

        prompts = []
        for header in headers[:max_images]:
            # Clean header
            clean_header = header.lstrip("#").strip()
            # Create simple prompt
            prompt = f"Professional illustration representing: {clean_header}"
            if style:
                prompt = f"{prompt}, in {style} style"
            prompts.append(prompt)

        # If no headers, create generic prompts
        if not prompts:
            prompts = [f"Professional blog illustration {i + 1}" for i in range(min(2, max_images))]

        return prompts[:max_images]
