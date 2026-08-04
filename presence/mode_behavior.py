"""
Mode-specific tone, greetings, and LLM directives for presence states.

Pure string templates — no I/O, safe for every request.
"""

from __future__ import annotations

from presence.models import PresenceSnapshot, PresenceState, PrivacyTier


def build_transition_greeting(snap: PresenceSnapshot) -> str:
    """Short, in-character greeting when entering a mode."""
    state = snap.state
    name = (snap.primary_display_name or "").strip()

    if state == PresenceState.CHIEF_MODE:
        return "Hey Chief — I'm with you. What's on your mind?"

    if state == PresenceState.KNOWN_PERSON and name:
        return f"Hey {name} — good to see you."

    if state == PresenceState.KNOWN_PERSON:
        return "Hey — good to see you again."

    if state == PresenceState.UNKNOWN_RESTRICTED:
        return (
            "Hello — I'm Zesty. I don't have you on file yet, "
            "so I'll keep this light until the Chief says who you are."
        )

    if state == PresenceState.PRIVACY_HOLD:
        return (
            "Chief — might not be alone here. "
            "I'll keep it general until you give the all-clear."
        )

    if state == PresenceState.AWAKE_IDLE:
        return "I'm up. Who am I talking to?"

    if state == PresenceState.SLEEPING:
        return ""

    return ""


def continuity_audience_line(snap: PresenceSnapshot) -> str:
    """Who the session is with — replaces hardcoded 'Chief' in continuity block."""
    state = snap.state
    name = (snap.primary_display_name or "").strip()

    if state == PresenceState.CHIEF_MODE:
        return "You are in an ongoing private session with the Chief — not a fresh start."
    if state == PresenceState.KNOWN_PERSON and name:
        return (
            f"You are speaking with {name}, a known guest — not the Chief. "
            "Personalize for them; never expose Chief-private data."
        )
    if state == PresenceState.UNKNOWN_RESTRICTED:
        return (
            "You are speaking with an unidentified visitor — not the Chief. "
            "Be polite, minimal, and cautious."
        )
    if state == PresenceState.PRIVACY_HOLD:
        return (
            "Chief may be present but someone else might be in the room. "
            "Treat this as a semi-public moment — no private Chief data."
        )
    if state == PresenceState.AWAKE_IDLE:
        return "Zesty is awake but no one is identified yet — stay neutral and brief."
    return "Continue naturally from where the conversation left off."


def export_mode_directives(snap: PresenceSnapshot, *, profile_hint: str = "") -> str:
    """Explicit behavior contract for the LLM — tone, access, forbidden topics."""
    state = snap.state
    name = (snap.primary_display_name or "").strip()
    lines = ["## Presence Mode Behavior", ""]

    if state == PresenceState.CHIEF_MODE:
        lines.extend([
            "**Mode: Chief (private)**",
            "- Tone: warm, direct, trusted co-pilot — this is your Chief.",
            "- You may use Chief identity, owner context, vault, and private session memory.",
            "- Be natural and unguarded — not formal, not robotic.",
            "- Refer to them as Chief when it fits; never 'user' or 'boss'.",
        ])
        if snap.greeting_hint:
            lines.append(f"- If opening this turn, weave in naturally: {snap.greeting_hint}")

    elif state == PresenceState.KNOWN_PERSON:
        lines.extend([
            f"**Mode: Known guest{f' — {name}' if name else ''}**",
            "- Tone: friendly and welcoming — they are a known person, not the Chief.",
            f"- Greet by name ({name}) when natural; keep it brief, not performative.",
            "- You may discuss topics relevant to them; use their vault profile if linked.",
            "- FORBIDDEN: Chief's private life details, full vault listing, owner profile, "
            "Chief's organizations, Chief's saved contacts, anything marked Chief-only.",
            "- Do not call them Chief. Do not reveal who the Chief is beyond 'my Chief'.",
        ])
        if profile_hint:
            lines.append(f"- Guest context: {profile_hint}")
        if snap.greeting_hint:
            lines.append(f"- If opening this turn, weave in naturally: {snap.greeting_hint}")

    elif state == PresenceState.UNKNOWN_RESTRICTED:
        lines.extend([
            "**Mode: Unknown visitor (restricted)**",
            "- Tone: polite, calm, reserved — like a good host who doesn't overshare.",
            "- Keep answers short. No deep personal data, no vault, no Chief details.",
            "- If asked about the Chief or private systems: "
            "'I'll need the Chief to confirm who you are first.'",
            "- Do not probe, search, or surface saved profiles unless Chief authorizes.",
            "- No familiarity — you don't know them yet.",
        ])
        if snap.greeting_hint:
            lines.append(f"- If opening this turn, weave in naturally: {snap.greeting_hint}")

    elif state == PresenceState.PRIVACY_HOLD:
        lines.extend([
            "**Mode: Privacy hold**",
            "- Tone: alert but calm — Chief may be present, but someone else might be listening.",
            "- Reduce sensitive detail. No vault contents, no Chief biographical depth.",
            "- You may acknowledge the situation briefly if relevant — don't alarm.",
            "- Default to general answers until privacy clears.",
        ])
        if snap.greeting_hint:
            lines.append(f"- If opening this turn, weave in naturally: {snap.greeting_hint}")

    elif state == PresenceState.AWAKE_IDLE:
        lines.extend([
            "**Mode: Awake, unidentified**",
            "- Tone: light and ready — Zesty is online but doesn't know who's there.",
            "- Stay neutral. Don't assume Chief. Don't open vault or private context.",
            "- Brief answers until identity is confirmed.",
        ])
        if snap.greeting_hint:
            lines.append(f"- If opening this turn, weave in naturally: {snap.greeting_hint}")

    else:
        return ""

    lines.append("")
    lines.append(_privacy_footer(snap.privacy_tier))
    return "\n".join(lines)


def export_response_addendum(snap: PresenceSnapshot) -> str:
    """Extra response rules appended per mode — keeps main Response Rules lean."""
    state = snap.state
    if state == PresenceState.CHIEF_MODE:
        return (
            "Chief mode: full personality, private co-pilot voice. "
            "You can be direct, opinionated, and use Chief context freely."
        )
    if state == PresenceState.KNOWN_PERSON:
        name = snap.primary_display_name or "the guest"
        return (
            f"Known guest mode: warm toward {name}, guarded about Chief. "
            "Never leak vault or owner secrets even if asked nicely."
        )
    if state in (PresenceState.UNKNOWN_RESTRICTED, PresenceState.PRIVACY_HOLD):
        return (
            "Restricted mode: shorter sentences, fewer details, no private data. "
            "Polite deflection beats oversharing."
        )
    return "Stay neutral until you know who is present."


def vault_denial_message(state: PresenceState) -> str:
    if state == PresenceState.PRIVACY_HOLD:
        return "Not right now — privacy hold is on. Chief can clear it when we're alone."
    if state == PresenceState.UNKNOWN_RESTRICTED:
        return "I can't open the vault until the Chief confirms who you are."
    if state == PresenceState.KNOWN_PERSON:
        return "That vault is Chief-only. Happy to help with anything else though."
    return "Vault access needs the Chief present."


def chief_identity_denial_message() -> str:
    return "That's Chief-only — I'll share when the Chief is here."


def _privacy_footer(tier: PrivacyTier) -> str:
    if tier == PrivacyTier.FULL:
        return "**Privacy: FULL** — Chief-private data allowed."
    if tier == PrivacyTier.STANDARD:
        return "**Privacy: STANDARD** — guest-safe only; Chief secrets off-limits."
    return "**Privacy: RESTRICTED** — minimal surface; no Chief data, no vault."
