"""
Amplifier Blog Creator App

Transforms ideas into polished blog posts with optional illustrations.
Coordinates style extraction, content generation, and illustration modules.
"""

from .blog_writer import BlogWriter
from .content_phase import ContentPhase
from .feedback import UserFeedbackHandler
from .illustration_phase import IllustrationPhase
from .session import SessionManager

__version__ = "0.1.0"

__all__ = [
    "BlogWriter",
    "ContentPhase",
    "IllustrationPhase",
    "UserFeedbackHandler",
    "SessionManager",
]
