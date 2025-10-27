"""Style extraction stage - analyzes writing samples to extract author style."""

import logging
import os
from pathlib import Path
from typing import Callable

from anthropic import AsyncAnthropic

from ...utils.llm_parsing import parse_llm_json
from ..models import StyleProfile

logger = logging.getLogger(__name__)


async def extract_style(
    writings_dir: Path, progress_callback: Callable[[str], None] | None = None
) -> StyleProfile:
    """Extract writing style from samples.

    Args:
        writings_dir: Directory containing writing samples
        progress_callback: Optional callback for progress updates

    Returns:
        StyleProfile with extracted characteristics

    Raises:
        ValueError: If no valid writings found
    """
    if progress_callback:
        progress_callback("Analyzing writing samples...")

    # Find all markdown files
    files = list(writings_dir.glob("**/*.md"))
    if not files:
        logger.warning(f"No markdown files found in {writings_dir}")
        if progress_callback:
            progress_callback("No samples found - using defaults")
        return _default_profile()

    logger.info(f"Found {len(files)} writing samples")

    # Read samples (limit to prevent context overflow)
    samples = []
    max_samples = 5
    max_chars_per_sample = 3000

    for file in files[:max_samples]:
        try:
            content = file.read_text()[:max_chars_per_sample]
            samples.append(f"=== {file.name} ===\n{content}")
        except Exception as e:
            logger.warning(f"Could not read {file}: {e}")

    if not samples:
        logger.warning("Could not read any writing samples")
        if progress_callback:
            progress_callback("Failed to read samples - using defaults")
        return _default_profile()

    # Extract style with AI
    combined_samples = "\n\n".join(samples)
    profile = await _analyze_with_ai(combined_samples)

    if progress_callback:
        progress_callback("Style extraction complete")

    return profile


async def _analyze_with_ai(samples: str) -> StyleProfile:
    """Analyze samples with AI to extract style.

    Args:
        samples: Combined writing samples

    Returns:
        Extracted style profile
    """
    prompt = f"""Analyze these writing samples to extract the author's style:

{samples}

Extract:
1. Overall tone (formal/casual/technical/conversational)
2. Vocabulary complexity level
3. Typical sentence structure patterns
4. Paragraph length preference
5. Common phrases or expressions (list)
6. Recurring writing patterns (list)
7. Voice preference (active/passive)
8. 3-5 example sentences that best capture the style (list)

Return as JSON with keys: tone, vocabulary_level, sentence_structure, paragraph_length,
common_phrases, writing_patterns, voice, examples"""

    try:
        client = AsyncAnthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))
        response = await client.messages.create(
            model="claude-3-5-haiku-20241022",
            max_tokens=2048,
            system="You are an expert writing style analyst.",
            messages=[{"role": "user", "content": prompt}],
        )

        content = response.content[0].text.strip()
        parsed = parse_llm_json(content, default=None)

        if parsed is None:
            logger.warning("Could not parse style response, using defaults")
            return _default_profile()

        # Ensure we have all required fields with defaults
        profile_data = {
            "tone": parsed.get("tone", "conversational"),
            "vocabulary_level": parsed.get("vocabulary_level", "moderate"),
            "sentence_structure": parsed.get("sentence_structure", "varied"),
            "paragraph_length": parsed.get("paragraph_length", "medium"),
            "common_phrases": parsed.get("common_phrases", []),
            "writing_patterns": parsed.get("writing_patterns", []),
            "voice": parsed.get("voice", "active"),
            "examples": parsed.get("examples", []),
        }

        return StyleProfile(**profile_data)

    except Exception as e:
        logger.error(f"Style extraction failed: {e}")
        return _default_profile()


def _default_profile() -> StyleProfile:
    """Return default style profile when extraction fails."""
    logger.info("Using default style profile")
    return StyleProfile(
        tone="conversational",
        vocabulary_level="moderate",
        sentence_structure="varied",
        paragraph_length="medium",
        common_phrases=[],
        writing_patterns=["introduction-body-conclusion", "problem-solution"],
        voice="active",
        examples=["Clear and direct communication.", "Focus on practical value."],
    )
