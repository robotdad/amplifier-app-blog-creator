"""Illustration Phase - Generate contextual images for blog posts.

Analyzes content to identify specific illustration points, generates contextual prompts,
creates images, and inserts them at appropriate line numbers in the markdown.
"""

import logging
from pathlib import Path

from amplifier_module_image_generation import ImageGenerator
from openai import OpenAI

from anthropic import AsyncAnthropic
from .utils.llm_parsing import parse_llm_json
import os

from .models import IllustrationPoint
from .models import ImagePrompt

logger = logging.getLogger(__name__)


class IllustrationPhase:
    """Orchestrates content-aware image generation and insertion for blog posts."""

    def __init__(self):
        """Initialize illustration phase."""
        self.image_generator = ImageGenerator()
        self.openai_client = OpenAI()

    async def run(
        self,
        article_path: Path,
        output_dir: Path,
        style: str | None = None,
        max_images: int = 3,
    ) -> Path:
        """Generate and insert contextual illustrations for blog post.

        Args:
            article_path: Path to blog markdown
            output_dir: Directory to save images
            style: Optional style description
            max_images: Maximum images to generate

        Returns:
            Path to illustrated markdown file
        """
        logger.info(f"Starting contextual illustration generation (max {max_images} images)")

        # Stage 1: Analyze content to identify illustration points
        points = await self._analyze_content(article_path, max_images)
        if not points:
            logger.warning("No illustration points identified")
            return article_path

        logger.info(f"✓ Identified {len(points)} illustration points")

        # Stage 2: Generate contextual prompts for each point
        prompts = await self._generate_prompts(points, article_path, style)
        logger.info(f"✓ Generated {len(prompts)} contextual prompts")

        # Stage 3: Generate images mapped to points
        images = await self._generate_images(prompts, output_dir)
        logger.info(f"✓ Generated {len(images)} images")

        if not images:
            logger.warning("No images generated")
            return article_path

        # Stage 4: Update markdown with images at specific line numbers
        illustrated_path = await self._update_markdown(article_path, images, points, output_dir)
        logger.info(f"✓ Created illustrated markdown: {illustrated_path.name}")

        return illustrated_path

    async def _analyze_content(self, article_path: Path, max_images: int) -> list[IllustrationPoint]:
        """Identify illustration points using clear distribution strategy.

        Distribution strategy:
        - 1 image: middle
        - 2 images: intro, closing
        - 3 images: intro, middle, closing (default)
        - 4+ images: evenly distributed segments

        Args:
            article_path: Path to markdown article
            max_images: Number of images to generate

        Returns:
            List of illustration points with balanced distribution
        """
        logger.info(f"Identifying {max_images} illustration points with balanced distribution...")

        content = article_path.read_text(encoding="utf-8")
        lines = content.split("\n")

        # Find all ## level sections (excluding ###)
        sections = []
        for i, line in enumerate(lines):
            if line.startswith("##") and not line.startswith("###"):
                title = line.lstrip("#").strip()
                sections.append((i, title))

        if not sections:
            logger.warning("No sections found, using fallback distribution")
            return self._create_fallback_points(lines, max_images)

        total_sections = len(sections)
        logger.info(f"Found {total_sections} sections")

        # Select sections based on number of images requested
        if max_images == 1:
            # Middle section
            selected = [total_sections // 2]
            logger.info("Distribution: middle")

        elif max_images == 2:
            # Intro and closing
            selected = [0, total_sections - 1]
            logger.info("Distribution: intro, closing")

        elif max_images == 3:
            # Intro, middle, closing
            middle = total_sections // 2
            selected = [0, middle, total_sections - 1]
            logger.info("Distribution: intro, middle, closing")

        else:
            # Evenly distribute across all sections
            step = total_sections / max_images
            selected = [int(i * step) for i in range(max_images)]
            logger.info(f"Distribution: evenly across {max_images} segments")

        # Create illustration points at selected sections
        points = []
        for idx in selected:
            if idx >= total_sections:
                idx = total_sections - 1

            line_num, section_title = sections[idx]

            # Get context around this point
            context_before = lines[max(0, line_num - 1)] if line_num > 0 else ""
            context_after = lines[min(len(lines) - 1, line_num + 1)] if line_num < len(lines) - 1 else ""

            points.append(IllustrationPoint(
                section_title=section_title,
                section_index=idx,
                line_number=line_num,
                context_before=context_before[:100],
                context_after=context_after[:100],
                importance="high",
                suggested_placement="before_section"
            ))

        logger.info(f"Selected sections: {[p.section_title for p in points]}")
        return points

    def _create_fallback_points(self, lines: list[str], max_images: int) -> list[IllustrationPoint]:
        """Create evenly spaced fallback points when no sections found.

        Args:
            lines: Article lines
            max_images: Number of points to create

        Returns:
            List of evenly spaced illustration points
        """
        total_lines = len(lines)
        step = total_lines // (max_images + 1)

        points = []
        for i in range(max_images):
            line_num = (i + 1) * step
            points.append(IllustrationPoint(
                section_title=f"Section {i+1}",
                section_index=i,
                line_number=line_num,
                context_before="",
                context_after="",
                importance="medium",
                suggested_placement="mid_section"
            ))

        return points

    async def _analyze_content_with_llm(self, article_path: Path, max_images: int) -> list[IllustrationPoint]:
        """DEPRECATED: LLM-based analysis (kept for reference).

        The LLM consistently clusters images at the beginning despite instructions.
        Using algorithmic distribution instead for reliable even spacing.
        """
        content = article_path.read_text(encoding="utf-8")

        prompt = f"""Analyze this markdown article and identify the {max_images} best places to add illustrations.

IMPORTANT: Distribute illustrations evenly throughout the ENTIRE article, not clustered at the beginning.

For each illustration point, provide:
- section_title: The section heading
- section_index: Index of the section (0-based)
- line_number: Approximate line number where image should be inserted
- context_before: 100 chars of text before the point
- context_after: 100 chars of text after the point
- importance: "high", "medium", or "low"
- suggested_placement: "before_section", "after_intro", or "mid_section"

Selection criteria (in order of priority):
1. Distribute evenly from beginning to end of article
2. Major section transitions that need visual breaks
3. Complex ideas or key concepts that images could clarify
4. Ensure at least one image in the latter half of the article

Article content:
```markdown
{content}
```

Return JSON with structure:
{{
  "illustration_points": [
    {{
      "section_title": "...",
      "section_index": 0,
      "line_number": 10,
      "context_before": "...",
      "context_after": "...",
      "importance": "high",
      "suggested_placement": "before_section"
    }}
  ]
}}"""

        try:
            response = self.openai_client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {
                        "role": "system",
                        "content": "You are an expert at identifying visual illustration opportunities in written content. Respond with JSON only.",
                    },
                    {"role": "user", "content": prompt},
                ],
                temperature=0.3,
            )

            message_content = response.choices[0].message.content
            if not message_content:
                raise ValueError("Empty response from OpenAI")

            analysis = parse_llm_json(message_content)

            if not isinstance(analysis, dict):
                raise ValueError("Expected dict response from LLM")

            points = []
            for point_data in analysis.get("illustration_points", [])[:max_images]:
                points.append(IllustrationPoint(**point_data))

            return points

        except Exception as e:
            logger.error(f"Failed to analyze content: {e}")
            return self._create_fallback_points(content, max_images)

    def _create_fallback_points(self, content: str, max_images: int) -> list[IllustrationPoint]:
        """Create basic illustration points as fallback.

        Args:
            content: Article content
            max_images: Maximum points to create

        Returns:
            List of fallback illustration points
        """
        lines = content.split("\n")
        headers = []
        for i, line in enumerate(lines):
            if line.startswith("#"):
                headers.append((i, line.strip("#").strip()))

        points = []
        for i, (line_num, title) in enumerate(headers[:max_images]):
            points.append(
                IllustrationPoint(
                    section_title=title,
                    section_index=i,
                    line_number=line_num,
                    context_before=lines[max(0, line_num - 2)] if line_num > 0 else "",
                    context_after=lines[min(len(lines) - 1, line_num + 2)],
                    importance="medium",
                    suggested_placement="before_section",
                )
            )

        return points

    async def _generate_prompts(
        self,
        points: list[IllustrationPoint],
        article_path: Path,
        style: str | None,
    ) -> list[ImagePrompt]:
        """Generate contextual image prompts for each illustration point.

        Args:
            points: List of identified illustration points
            article_path: Path to original article for context
            style: Optional style description

        Returns:
            List of image prompts with full context
        """
        logger.info(f"Generating contextual prompts for {len(points)} points...")

        article_content = article_path.read_text(encoding="utf-8")[:4000]
        style_description = style or self._get_default_style()

        prompts = []
        for i, point in enumerate(points):
            try:
                prompt = await self._generate_single_prompt(point, i, article_content, style_description)
                prompts.append(prompt)
                logger.info(f"  Generated prompt {i + 1}/{len(points)}")
            except Exception as e:
                logger.error(f"  Failed to generate prompt {i + 1}: {e}")
                prompts.append(self._create_fallback_prompt(point, i))

        return prompts

    async def _generate_single_prompt(
        self,
        point: IllustrationPoint,
        index: int,
        article_context: str,
        style_description: str,
    ) -> ImagePrompt:
        """Generate a single contextual image prompt.

        Args:
            point: Illustration point
            index: Point index
            article_context: Article content for context
            style_description: Style requirements

        Returns:
            Generated image prompt
        """
        prompt_text = f"""Generate an image prompt for an illustration at this point in an article.

Article context (truncated):
{article_context}

Illustration point:
- Section: {point.section_title}
- Context before: {point.context_before}
- Context after: {point.context_after}
- Placement: {point.suggested_placement}
- Importance: {point.importance}

Style requirements:
{style_description}

Create a detailed image generation prompt that:
1. Relates directly to the content
2. Is appropriate for AI image generation (no text, clear subjects)
3. Maintains consistent style with other images
4. Avoids controversial or problematic content

Return JSON with:
{{
  "base_prompt": "Main description of the image",
  "style_modifiers": ["modifier1", "modifier2"],
  "full_prompt": "Complete prompt combining base and modifiers",
  "metadata": {{
    "mood": "...",
    "color_palette": "...",
    "composition": "..."
  }}
}}"""

        client = AsyncAnthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))

        response = await client.messages.create(
            model="claude-3-5-haiku-20241022",
            max_tokens=2048,
            system="You are an expert at creating image generation prompts. Respond with JSON only.",
            messages=[{"role": "user", "content": prompt_text}]
        )

        if not response.content:
            raise RuntimeError("Empty response from Claude")

        message_content = response.content[0].text
        parsed = parse_llm_json(message_content)

        if not isinstance(parsed, dict):
            raise ValueError("Expected dict response from LLM")

        return ImagePrompt(
            illustration_id=f"illustration-{index + 1}",
            point=point,
            base_prompt=parsed.get("base_prompt", "Abstract illustration"),
            style_modifiers=parsed.get("style_modifiers", []),
            full_prompt=parsed.get("full_prompt", "Abstract illustration"),
            metadata=parsed.get("metadata", {}),
        )

    def _create_fallback_prompt(self, point: IllustrationPoint, index: int) -> ImagePrompt:
        """Create a basic fallback prompt.

        Args:
            point: Illustration point
            index: Point index

        Returns:
            Fallback image prompt
        """
        return ImagePrompt(
            illustration_id=f"illustration-{index + 1}",
            point=point,
            base_prompt=f"Abstract illustration for {point.section_title}",
            style_modifiers=["minimalist", "professional", "technical"],
            full_prompt=f"Abstract minimalist professional technical illustration for {point.section_title}",
            metadata={"fallback": "true"},
        )

    def _get_default_style(self) -> str:
        """Get default style description.

        Returns:
            Default style description
        """
        return """Modern, clean illustration style:
- Minimalist with bold colors
- Professional and technical aesthetic
- Abstract or conceptual rather than literal
- Consistent color palette across all images
- High contrast for web viewing
- No text or words in images"""

    async def _generate_images(
        self,
        prompts: list[ImagePrompt],
        output_dir: Path,
    ) -> dict[str, Path]:
        """Generate images for each prompt.

        Args:
            prompts: List of image prompts
            output_dir: Directory to save images

        Returns:
            Dict mapping illustration_id to image path
        """
        logger.info(f"Generating {len(prompts)} images...")

        output_dir.mkdir(parents=True, exist_ok=True)
        images = {}

        for _i, prompt in enumerate(prompts, 1):
            try:
                image_path = output_dir / f"{prompt.illustration_id}.png"

                result = await self.image_generator.generate(
                    prompt=prompt.full_prompt,
                    output_path=image_path,
                    preferred_api="gptimage",
                )

                if result.success:
                    images[prompt.illustration_id] = result.local_path
                    logger.info(f"  ✓ Generated {prompt.illustration_id} (cost: ${result.cost:.4f})")
                else:
                    logger.error(f"  ✗ Failed {prompt.illustration_id}: {result.error}")

            except Exception as e:
                logger.error(f"  ✗ Failed {prompt.illustration_id}: {e}")

        return images

    async def _update_markdown(
        self,
        article_path: Path,
        images: dict[str, Path],
        points: list[IllustrationPoint],
        output_dir: Path,
    ) -> Path:
        """Update markdown with images at specific line numbers.

        Inserts images at contextually appropriate positions based on illustration points.
        Uses reverse order insertion to maintain line numbers.

        Args:
            article_path: Original article path
            images: Dict mapping illustration_id to image path
            points: Original illustration points
            output_dir: Output directory

        Returns:
            Path to illustrated markdown file
        """
        logger.info(f"Inserting {len(images)} images into markdown...")

        content = article_path.read_text(encoding="utf-8")
        lines = content.split("\n")

        # Sort points by line number in reverse to insert bottom-up
        sorted_items = sorted(
            [(point, images.get(f"illustration-{i + 1}")) for i, point in enumerate(points)],
            key=lambda x: x[0].line_number,
            reverse=True,
        )

        # Insert images at appropriate positions
        for point, image_path in sorted_items:
            if not image_path:
                continue

            # Create image markdown
            relative_path = f"./images/{image_path.name}"
            image_markdown = self._create_image_markdown(relative_path, point)

            # Find insertion line
            insert_line = self._find_insertion_line(lines, point)

            # Insert the markdown
            if 0 <= insert_line < len(lines):
                lines.insert(insert_line, image_markdown)
                logger.info(f"  ✓ Inserted at line {insert_line} ({point.suggested_placement})")

        # Save illustrated markdown
        output_path = output_dir.parent / f"illustrated_{article_path.name}"
        output_path.write_text("\n".join(lines), encoding="utf-8")

        return output_path

    def _create_image_markdown(self, image_path: str, point: IllustrationPoint) -> str:
        """Create markdown for an image.

        Args:
            image_path: Relative path to image
            point: Illustration point

        Returns:
            Markdown string for image
        """
        return f'\n<img src="{image_path}" alt="{point.section_title}" width="50%">\n'

    def _find_insertion_line(self, lines: list[str], point: IllustrationPoint) -> int:
        """Find the best line to insert an image.

        Args:
            lines: Article lines
            point: Illustration point

        Returns:
            Line index for insertion
        """
        target = point.line_number

        # Adjust based on placement preference
        if point.suggested_placement == "before_section":
            # Find the section header and insert before it
            for i in range(max(0, target - 5), min(len(lines), target + 5)):
                if lines[i].startswith("#") and point.section_title in lines[i]:
                    return i
        elif point.suggested_placement == "after_intro":
            # Insert after first paragraph of section
            for i in range(target, min(len(lines), target + 20)):
                if not lines[i].strip() and i > target:
                    return i + 1

        # Default: insert at the target line
        return min(target, len(lines))
