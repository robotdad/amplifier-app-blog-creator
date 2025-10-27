"""
Amplifier Blog Creator App

Transforms ideas into polished blog posts with optional illustrations.
Stage-based architecture with core business logic and CLI adapter.
"""

from .core.models import ReviewResult
from .core.models import RevisionFeedback
from .core.models import StyleProfile
from .core.workflow import BlogCreatorWorkflow
from .session import SessionManager

__version__ = "0.1.0"

__all__ = [
    "BlogCreatorWorkflow",
    "SessionManager",
    "StyleProfile",
    "ReviewResult",
    "RevisionFeedback",
]
