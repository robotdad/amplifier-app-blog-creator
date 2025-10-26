"""Data models for blog creator."""

from typing import Literal

from pydantic import BaseModel
from pydantic import Field


class IllustrationPoint(BaseModel):
    """A point in the article where an illustration should be added."""

    section_title: str
    section_index: int
    line_number: int
    context_before: str
    context_after: str
    importance: Literal["high", "medium", "low"]
    suggested_placement: Literal["before_section", "after_intro", "mid_section"]


class ImagePrompt(BaseModel):
    """An image generation prompt for a specific illustration point."""

    illustration_id: str
    point: IllustrationPoint
    base_prompt: str
    style_modifiers: list[str] = Field(default_factory=list)
    full_prompt: str
    metadata: dict[str, str] = Field(default_factory=dict)
