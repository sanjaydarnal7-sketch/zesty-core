"""
Zesty OS Presence & Multi-user Identity foundation.

Flask era: stub adapters, manual/API wake, identity registry on disk.
Electron era: swap adapters for native wake word, camera, and voice ID.
"""

from presence.commands import (
    IntroductionCommand,
    SimulateAction,
    SimulateCommand,
    parse_introduction,
    parse_simulate_command,
)
from presence.identity_registry import IdentityRegistry
from presence.models import (
    BiometricRefs,
    DetectionResult,
    IdentityRole,
    PersonIdentity,
    PresenceSnapshot,
    PresenceState,
    PrivacyTier,
    WakeSource,
)
from presence.presence_manager import PresenceManager
from presence.profile_bridge import IdentityProfileBridge

__all__ = [
    "BiometricRefs",
    "DetectionResult",
    "IdentityProfileBridge",
    "IdentityRegistry",
    "IdentityRole",
    "IntroductionCommand",
    "PersonIdentity",
    "PresenceManager",
    "PresenceSnapshot",
    "PresenceState",
    "PrivacyTier",
    "SimulateAction",
    "SimulateCommand",
    "WakeSource",
    "parse_introduction",
    "parse_simulate_command",
]
