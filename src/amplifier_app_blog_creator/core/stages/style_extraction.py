"""Style extraction stage - wraps amplifier-module-style-extraction."""

from pathlib import Path
from typing import Callable

from amplifier_module_style_extraction.core import StyleExtractor

from ..models import StyleProfile


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

    extractor = StyleExtractor()
    profile = await extractor.extract_style(writings_dir)

    if progress_callback:
        progress_callback("Style extraction complete")

    return StyleProfile(**profile.model_dump())
