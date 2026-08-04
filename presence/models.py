"""
Data models for Zesty OS Presence & Multi-user Identity.

These types are transport- and storage-agnostic so Flask, Electron, and
future native wake-word / camera services can share the same contract.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any


class PresenceState(str, Enum):
    """High-level runtime presence states for Zesty OS."""

    SLEEPING = "sleeping"
    AWAKE_IDLE = "awake_idle"
    CHIEF_MODE = "chief_mode"
    KNOWN_PERSON = "known_person"
    UNKNOWN_RESTRICTED = "unknown_restricted"
    PRIVACY_HOLD = "privacy_hold"


class IdentityRole(str, Enum):
    """Who the detected person is relative to Zesty."""

    CHIEF = "chief"
    KNOWN = "known"
    GUEST = "guest"
    UNKNOWN = "unknown"


class PrivacyTier(str, Enum):
    """What data/actions are allowed for the current session."""

    FULL = "full"          # Chief — private mode, full memory, vault, owner data
    STANDARD = "standard"  # Known person — personalized, no Chief-private data
    RESTRICTED = "restricted"  # Unknown / privacy hold — minimal surface


class WakeSource(str, Enum):
    """How Zesty was activated."""

    WAKE_WORD = "wake_word"
    MANUAL = "manual"
    API = "api"
    CAMERA = "camera"


@dataclass
class BiometricRefs:
    """Future hooks for face/voice embeddings — paths or external store IDs."""

    face_embedding_id: str = ""
    face_embedding_path: str = ""
    voice_embedding_id: str = ""
    voice_sample_path: str = ""
    enrollment_confidence: float = 0.0
    last_match_confidence: float = 0.0

    def to_dict(self) -> dict[str, Any]:
        return {
            "face_embedding_id": self.face_embedding_id,
            "face_embedding_path": self.face_embedding_path,
            "voice_embedding_id": self.voice_embedding_id,
            "voice_sample_path": self.voice_sample_path,
            "enrollment_confidence": self.enrollment_confidence,
            "last_match_confidence": self.last_match_confidence,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any] | None) -> "BiometricRefs":
        data = data or {}
        return cls(
            face_embedding_id=str(data.get("face_embedding_id") or ""),
            face_embedding_path=str(data.get("face_embedding_path") or ""),
            voice_embedding_id=str(data.get("voice_embedding_id") or ""),
            voice_sample_path=str(data.get("voice_sample_path") or ""),
            enrollment_confidence=float(data.get("enrollment_confidence") or 0.0),
            last_match_confidence=float(data.get("last_match_confidence") or 0.0),
        )


@dataclass
class PersonIdentity:
    """A known person in the identity registry."""

    identity_id: str
    display_name: str
    role: IdentityRole = IdentityRole.KNOWN
    privacy_tier: PrivacyTier = PrivacyTier.STANDARD
    saved_profile_id: str = ""
    owner_profile_ref: str = ""
    biometrics: BiometricRefs = field(default_factory=BiometricRefs)
    aliases: list[str] = field(default_factory=list)
    notes: str = ""
    enrolled_at: str = ""
    last_seen_at: str = ""
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "identity_id": self.identity_id,
            "display_name": self.display_name,
            "role": self.role.value,
            "privacy_tier": self.privacy_tier.value,
            "saved_profile_id": self.saved_profile_id,
            "owner_profile_ref": self.owner_profile_ref,
            "biometrics": self.biometrics.to_dict(),
            "aliases": list(self.aliases),
            "notes": self.notes,
            "enrolled_at": self.enrolled_at,
            "last_seen_at": self.last_seen_at,
            "metadata": dict(self.metadata),
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "PersonIdentity":
        return cls(
            identity_id=str(data.get("identity_id") or ""),
            display_name=str(data.get("display_name") or ""),
            role=IdentityRole(data.get("role") or IdentityRole.KNOWN.value),
            privacy_tier=PrivacyTier(data.get("privacy_tier") or PrivacyTier.STANDARD.value),
            saved_profile_id=str(data.get("saved_profile_id") or ""),
            owner_profile_ref=str(data.get("owner_profile_ref") or ""),
            biometrics=BiometricRefs.from_dict(data.get("biometrics")),
            aliases=list(data.get("aliases") or []),
            notes=str(data.get("notes") or ""),
            enrolled_at=str(data.get("enrolled_at") or ""),
            last_seen_at=str(data.get("last_seen_at") or ""),
            metadata=dict(data.get("metadata") or {}),
        )


@dataclass
class DetectionResult:
    """Normalized output from a face or voice adapter (future)."""

    modality: str  # face | voice
    identity_id: str = ""
    display_name: str = ""
    role: IdentityRole = IdentityRole.UNKNOWN
    confidence: float = 0.0
    is_secondary: bool = False
    raw: dict[str, Any] = field(default_factory=dict)


@dataclass
class PresenceSnapshot:
    """Point-in-time presence state exposed to UI, API, and prompt assembly."""

    state: PresenceState = PresenceState.AWAKE_IDLE
    privacy_tier: PrivacyTier = PrivacyTier.STANDARD
    primary_identity_id: str = ""
    primary_display_name: str = ""
    primary_role: IdentityRole = IdentityRole.UNKNOWN
    secondary_detected: bool = False
    wake_source: WakeSource = WakeSource.MANUAL
    greeting_hint: str = ""
    restricted_reason: str = ""
    last_event: str = ""
    updated_at: str = field(default_factory=lambda: datetime.now().isoformat(timespec="seconds"))

    def to_dict(self) -> dict[str, Any]:
        return {
            "state": self.state.value,
            "privacy_tier": self.privacy_tier.value,
            "primary_identity_id": self.primary_identity_id,
            "primary_display_name": self.primary_display_name,
            "primary_role": self.primary_role.value,
            "secondary_detected": self.secondary_detected,
            "wake_source": self.wake_source.value,
            "greeting_hint": self.greeting_hint,
            "restricted_reason": self.restricted_reason,
            "last_event": self.last_event,
            "updated_at": self.updated_at,
        }
