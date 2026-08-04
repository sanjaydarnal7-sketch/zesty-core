"""
Presence Manager — state machine for wake, identity, and privacy modes.

Flask/browser era: defaults to AWAKE_IDLE with stub adapters.
Electron era: plug in real wake-word, camera, and voice adapters.
"""

from __future__ import annotations

from datetime import datetime
from typing import Any

from presence.adapters.stub import (
    StubFaceRecognitionAdapter,
    StubVoiceIdentityAdapter,
    StubWakeWordAdapter,
)
from presence.commands import SimulateAction, SimulateCommand
from presence.identity_registry import IdentityRegistry
from presence.mode_behavior import (
    build_transition_greeting,
    chief_identity_denial_message,
    continuity_audience_line,
    export_mode_directives,
    export_response_addendum,
    vault_denial_message,
)
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

if False:  # pragma: no cover — import cycle guard for type hints only
    from presence.profile_bridge import IdentityProfileBridge


class PresenceManager:
    """Orchestrates presence states and privacy boundaries."""

    WAKE_PHRASE = "hey zesty"

    def __init__(
        self,
        registry: IdentityRegistry | None = None,
        *,
        wake_adapter=None,
        face_adapter=None,
        voice_adapter=None,
        profile_bridge=None,
        owner_display_name: str = "Sanjay Darnal",
    ) -> None:
        self.registry = registry or IdentityRegistry()
        self.wake_adapter = wake_adapter or StubWakeWordAdapter()
        self.face_adapter = face_adapter or StubFaceRecognitionAdapter()
        self.voice_adapter = voice_adapter or StubVoiceIdentityAdapter()
        self.profile_bridge = profile_bridge
        self._pending_greeting: str = ""
        chief = self.registry.ensure_chief(display_name=owner_display_name)
        # Flask/browser era: no sensors yet — default to Chief full access.
        # Electron will call start_listening() and drive real state transitions.
        self._snapshot = PresenceSnapshot(
            state=PresenceState.CHIEF_MODE,
            privacy_tier=PrivacyTier.FULL,
            primary_identity_id=chief.identity_id,
            primary_display_name=chief.display_name,
            primary_role=IdentityRole.CHIEF,
            wake_source=WakeSource.MANUAL,
            last_event="init:flask_chief_default",
        )

    @property
    def snapshot(self) -> PresenceSnapshot:
        return self._snapshot

    def get_privacy_tier(self) -> PrivacyTier:
        return self._snapshot.privacy_tier

    def is_chief_present(self) -> bool:
        return self._snapshot.state == PresenceState.CHIEF_MODE

    def should_restrict_private_data(self) -> bool:
        """True when Chief-private data must not be exposed."""
        return self._snapshot.privacy_tier != PrivacyTier.FULL

    def allows_full_vault(self) -> bool:
        return self._snapshot.privacy_tier == PrivacyTier.FULL

    def allows_chief_identity(self) -> bool:
        return self._snapshot.privacy_tier == PrivacyTier.FULL

    def allows_vault_commands(self) -> bool:
        return self._snapshot.privacy_tier == PrivacyTier.FULL

    def allows_probe_context(self, probe: dict | None) -> bool:
        if not probe:
            return False
        if self._snapshot.privacy_tier == PrivacyTier.FULL:
            return True
        if self._snapshot.state == PresenceState.KNOWN_PERSON:
            probe_name = (probe.get("name") or "").strip().lower()
            person = (self._snapshot.primary_display_name or "").strip().lower()
            if person and probe_name:
                return person in probe_name or probe_name in person
        return False

    def consume_pending_greeting(self) -> str:
        greeting = self._pending_greeting
        self._pending_greeting = ""
        return greeting

    def vault_denial_reply(self) -> str:
        return vault_denial_message(self._snapshot.state)

    def chief_identity_denial_reply(self) -> str:
        return chief_identity_denial_message()

    # ------------------------------------------------------------------
    # Lifecycle events (called by future Electron / sensor layer)
    # ------------------------------------------------------------------

    def start_listening(self) -> None:
        self.wake_adapter.start()
        self._transition(
            PresenceState.SLEEPING,
            PrivacyTier.RESTRICTED,
            event="start_listening",
            greeting_hint="",
        )

    def stop_listening(self) -> None:
        self.wake_adapter.stop()

    def handle_manual_wake(self) -> PresenceSnapshot:
        return self._wake(WakeSource.MANUAL)

    def handle_wake_word(self, phrase: str = "") -> PresenceSnapshot:
        return self._wake(WakeSource.WAKE_WORD, phrase=phrase)

    def handle_api_wake(self) -> PresenceSnapshot:
        return self._wake(WakeSource.API)

    def _wake(self, source: WakeSource, *, phrase: str = "") -> PresenceSnapshot:
        hint = "Zesty online — ready when you are, Chief."
        if source == WakeSource.WAKE_WORD:
            hint = "Wake word detected. Zesty is listening."
        return self._transition(
            PresenceState.AWAKE_IDLE,
            PrivacyTier.STANDARD,
            event=f"wake:{source.value}",
            wake_source=source,
            greeting_hint=hint,
            restricted_reason="",
        )

    def handle_face_scan(self, result: DetectionResult | None = None) -> PresenceSnapshot:
        """Process a face scan — uses adapter if result not supplied."""
        detection = result or self.face_adapter.scan_frame()
        if not detection:
            return self._transition(
                PresenceState.AWAKE_IDLE,
                PrivacyTier.STANDARD,
                event="face_scan:no_match",
                greeting_hint="I don't have a visual match yet.",
            )

        if detection.is_secondary and self._snapshot.state == PresenceState.CHIEF_MODE:
            return self._enter_privacy_hold("secondary_face_detected")

        return self._apply_detection(detection, event_prefix="face_scan")

    def handle_voice_detection(self, result: DetectionResult | None = None) -> PresenceSnapshot:
        detection = result or self.voice_adapter.identify_speaker()
        if not detection:
            return self.snapshot

        if detection.is_secondary and self._snapshot.state == PresenceState.CHIEF_MODE:
            return self._enter_privacy_hold("secondary_voice_detected")

        return self._apply_detection(detection, event_prefix="voice_scan")

    def handle_unknown_person(self) -> PresenceSnapshot:
        return self._transition(
            PresenceState.UNKNOWN_RESTRICTED,
            PrivacyTier.RESTRICTED,
            event="unknown_person",
            primary_role=IdentityRole.UNKNOWN,
            greeting_hint=(
                "I don't recognize you yet. I'll keep this session restricted "
                "until the Chief confirms who you are."
            ),
            restricted_reason="unidentified_visitor",
        )

    def handle_chief_onboard(
        self,
        display_name: str,
        *,
        saved_profile_id: str = "",
        face_embedding_id: str = "",
        voice_embedding_id: str = "",
    ) -> PersonIdentity:
        """Chief tells Zesty who an unknown person is."""
        ident, _ = self.introduce_person(
            display_name,
            saved_profile_id=saved_profile_id,
            face_embedding_id=face_embedding_id,
            voice_embedding_id=voice_embedding_id,
        )
        return ident

    def introduce_person(
        self,
        display_name: str,
        *,
        saved_profile_id: str = "",
        face_embedding_id: str = "",
        voice_embedding_id: str = "",
    ) -> tuple[PersonIdentity, str]:
        """
        Chief introduces someone — link vault profile if found, update presence.

        Returns (identity, voice_reply_hint).
        """
        profile_id = saved_profile_id
        if not profile_id and self.profile_bridge:
            found_id, _ = self.profile_bridge.find_profile_for_name(display_name)
            profile_id = found_id

        ident, created = self.registry.introduce_person(
            display_name,
            saved_profile_id=profile_id,
            biometrics=BiometricRefs(
                face_embedding_id=face_embedding_id,
                voice_embedding_id=voice_embedding_id,
            ),
        )
        self._apply_identity(ident, confidence=1.0, event="chief_introduce")

        greeting = build_transition_greeting(self._snapshot)
        if profile_id:
            link_note = " I've linked their vault profile."
        elif created:
            link_note = " I'll remember them."
        else:
            link_note = " They're already on file."

        reply = f"Got it, Chief.{link_note} {greeting}".strip()
        self._pending_greeting = ""
        return ident, reply

    def run_simulate(self, command: SimulateCommand) -> tuple[PresenceSnapshot, str]:
        """Apply a lightweight simulated presence event — no sensor I/O."""
        action = command.action
        name = command.name

        if action == SimulateAction.WAKE:
            snap = self.handle_api_wake()
            reply = build_transition_greeting(snap) or "I'm up."
            self._pending_greeting = ""
            return snap, reply

        if action == SimulateAction.SLEEP:
            snap = self.sleep()
            self._pending_greeting = ""
            return snap, "Going quiet."

        if action == SimulateAction.CHIEF:
            chief = self.registry.get_chief()
            if not chief:
                return self.snapshot, "No Chief identity in registry."
            snap = self._apply_identity(chief, 1.0, event="simulate:chief")
            reply = build_transition_greeting(snap)
            self._pending_greeting = ""
            return snap, reply

        if action == SimulateAction.KNOWN:
            if not name:
                return self.snapshot, "Say: presence known <name>"
            ident = self.registry.find_by_display_name(name)
            if not ident:
                ident, _ = self.registry.introduce_person(name)
            snap = self._apply_identity(ident, 0.95, event="simulate:known")
            reply = build_transition_greeting(snap)
            self._pending_greeting = ""
            return snap, reply

        if action == SimulateAction.UNKNOWN:
            snap = self.handle_unknown_person()
            reply = build_transition_greeting(snap)
            self._pending_greeting = ""
            return snap, reply

        if action == SimulateAction.PRIVACY_HOLD:
            if self._snapshot.state != PresenceState.CHIEF_MODE:
                chief = self.registry.get_chief()
                if chief:
                    self._apply_identity(chief, 1.0, event="simulate:chief_setup")
            snap = self._enter_privacy_hold("simulate:secondary_person")
            reply = build_transition_greeting(snap)
            self._pending_greeting = ""
            return snap, reply

        if action == SimulateAction.RESET:
            chief = self.registry.get_chief()
            if chief:
                snap = self._apply_identity(chief, 1.0, event="simulate:reset")
            else:
                snap = self._transition(
                    PresenceState.AWAKE_IDLE,
                    PrivacyTier.STANDARD,
                    event="simulate:reset",
                )
            reply = build_transition_greeting(snap) or "Back to default."
            self._pending_greeting = ""
            return snap, reply

        if action == SimulateAction.STATUS:
            snap = self.snapshot
            return snap, (
                f"Presence: {snap.state.value} | privacy={snap.privacy_tier.value}"
                + (f" | person={snap.primary_display_name}" if snap.primary_display_name else "")
            )

        return self.snapshot, "Unknown simulate action."

    def clear_privacy_hold(self) -> PresenceSnapshot:
        chief = self.registry.get_chief()
        if chief:
            return self._apply_identity(chief, confidence=1.0, event="privacy_hold_cleared")
        return self._transition(
            PresenceState.AWAKE_IDLE,
            PrivacyTier.STANDARD,
            event="privacy_hold_cleared",
        )

    def sleep(self) -> PresenceSnapshot:
        return self._transition(
            PresenceState.SLEEPING,
            PrivacyTier.RESTRICTED,
            event="sleep",
            greeting_hint="",
            primary_identity_id="",
            primary_display_name="",
        )

    # ------------------------------------------------------------------
    # Prompt / API integration
    # ------------------------------------------------------------------

    def export_for_prompt(self) -> str:
        snap = self._snapshot
        if snap.state == PresenceState.SLEEPING:
            return ""

        profile_hint = self._active_profile_hint()
        mode_block = export_mode_directives(snap, profile_hint=profile_hint)
        if mode_block:
            return mode_block

        return ""

    def export_response_addendum(self) -> str:
        return export_response_addendum(self._snapshot)

    def continuity_audience_line(self) -> str:
        return continuity_audience_line(self._snapshot)

    def to_api_payload(self) -> dict[str, Any]:
        payload = dict(self._snapshot.to_dict())
        if self._snapshot.primary_identity_id:
            ident = self.registry.get(self._snapshot.primary_identity_id)
            if ident and ident.saved_profile_id:
                payload["linked_profile_id"] = ident.saved_profile_id
        return payload

    def _active_profile_hint(self) -> str:
        """Fast vault context for the person in focus — cached profile lookup only."""
        snap = self._snapshot
        if snap.state not in (PresenceState.KNOWN_PERSON, PresenceState.CHIEF_MODE):
            return ""
        if not snap.primary_identity_id or not self.profile_bridge:
            return ""
        profile = self.profile_bridge.get_profile_for_identity_id(snap.primary_identity_id)
        return self.profile_bridge.format_brief(profile)

    def poll_sensors(self) -> PresenceSnapshot:
        """Future always-on loop: wake word poll. No-op in stub era."""
        wake = self.wake_adapter.poll_wake()
        if wake:
            return self._wake(wake)
        return self.snapshot

    # ------------------------------------------------------------------
    # Internal state machine
    # ------------------------------------------------------------------

    def _apply_detection(self, detection: DetectionResult, *, event_prefix: str) -> PresenceSnapshot:
        if detection.identity_id:
            ident = self.registry.get(detection.identity_id)
            if ident:
                return self._apply_identity(ident, detection.confidence, event=f"{event_prefix}:match")

        if detection.role == IdentityRole.CHIEF or detection.display_name.lower() in (
            "chief",
            "sanjay darnal",
        ):
            chief = self.registry.get_chief()
            if chief:
                return self._apply_identity(chief, detection.confidence, event=f"{event_prefix}:chief")

        if detection.display_name:
            ident = self.registry.find_by_display_name(detection.display_name)
            if ident:
                return self._apply_identity(ident, detection.confidence, event=f"{event_prefix}:name_match")

        return self.handle_unknown_person()

    def _apply_identity(
        self,
        ident: PersonIdentity,
        confidence: float,
        *,
        event: str,
    ) -> PresenceSnapshot:
        self.registry.touch_seen(ident.identity_id, match_confidence=confidence, persist=False)

        if ident.role == IdentityRole.CHIEF:
            snap = self._transition(
                PresenceState.CHIEF_MODE,
                PrivacyTier.FULL,
                event=event,
                primary_identity_id=ident.identity_id,
                primary_display_name=ident.display_name,
                primary_role=IdentityRole.CHIEF,
                greeting_hint="Welcome back, Chief.",
            )
            self._pending_greeting = build_transition_greeting(snap)
            return snap

        snap = self._transition(
            PresenceState.KNOWN_PERSON,
            ident.privacy_tier,
            event=event,
            primary_identity_id=ident.identity_id,
            primary_display_name=ident.display_name,
            primary_role=ident.role,
            greeting_hint=f"Good to see you, {ident.display_name}.",
        )
        self._pending_greeting = build_transition_greeting(snap)
        return snap

    def _enter_privacy_hold(self, reason: str) -> PresenceSnapshot:
        snap = self._snapshot
        result = self._transition(
            PresenceState.PRIVACY_HOLD,
            PrivacyTier.RESTRICTED,
            event=reason,
            secondary_detected=True,
            restricted_reason=reason,
            greeting_hint=(
                "Chief, someone else may be in the room — "
                "I've switched to restricted mode."
            ),
            primary_identity_id=snap.primary_identity_id,
            primary_display_name=snap.primary_display_name,
            primary_role=snap.primary_role,
        )
        self._pending_greeting = build_transition_greeting(result)
        return result

    def _transition(
        self,
        state: PresenceState,
        privacy_tier: PrivacyTier,
        *,
        event: str,
        primary_identity_id: str = "",
        primary_display_name: str = "",
        primary_role: IdentityRole = IdentityRole.UNKNOWN,
        secondary_detected: bool = False,
        wake_source: WakeSource | None = None,
        greeting_hint: str = "",
        restricted_reason: str = "",
    ) -> PresenceSnapshot:
        prev_state = self._snapshot.state
        self._snapshot = PresenceSnapshot(
            state=state,
            privacy_tier=privacy_tier,
            primary_identity_id=primary_identity_id or self._snapshot.primary_identity_id,
            primary_display_name=primary_display_name or self._snapshot.primary_display_name,
            primary_role=(
                primary_role
                if primary_display_name or primary_identity_id
                else self._snapshot.primary_role
            ),
            secondary_detected=secondary_detected,
            wake_source=wake_source or self._snapshot.wake_source,
            greeting_hint=greeting_hint,
            restricted_reason=restricted_reason,
            last_event=event,
            updated_at=datetime.now().isoformat(timespec="seconds"),
        )
        if state != prev_state and state in (
            PresenceState.UNKNOWN_RESTRICTED,
            PresenceState.AWAKE_IDLE,
        ):
            self._pending_greeting = build_transition_greeting(self._snapshot)
        return self._snapshot
