"""
Learning Engine Package
"""

from .learning_engine import LearningEngine
from .models import Fact, LearningResult

__version__ = "2.0.0"

__all__ = [
    "LearningEngine",
    "Fact",
    "LearningResult",
]
