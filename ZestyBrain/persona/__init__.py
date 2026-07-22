"""
Zesty Persona Package
"""

from .persona_engine import PersonaEngine
from .persona_loader import PersonaLoader
from .behavior_engine import BehaviorEngine
from .language_engine import detect as detect_language
from .conversation_director import ConversationDirector
from .prompt_builder import PromptBuilder
from .identity import IDENTITY
from .user_profile import USER_PROFILE

__version__ = "2.0.0"

__all__ = [
    "PersonaEngine",
    "PersonaLoader",
    "BehaviorEngine",
    "detect_language",
    "ConversationDirector",
    "PromptBuilder",
    "IDENTITY",
    "USER_PROFILE",
]
