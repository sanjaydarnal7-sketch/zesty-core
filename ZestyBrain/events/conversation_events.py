"""
Zesty OS
Conversation Events
Version: 1.0

ADR-004

Defines all runtime events used by the
Conversation Orchestrator.
"""

from __future__ import annotations

# ---------------------------------------------------------
# Session Lifecycle
# ---------------------------------------------------------

SESSION_STARTED = "SESSION_STARTED"
SESSION_ENDED = "SESSION_ENDED"

# ---------------------------------------------------------
# Speech Events
# ---------------------------------------------------------

SPEECH_STARTED = "SPEECH_STARTED"
SPEECH_PARTIAL = "SPEECH_PARTIAL"
SPEECH_FINISHED = "SPEECH_FINISHED"

# ---------------------------------------------------------
# Reflex Events
# ---------------------------------------------------------

BACKCHANNEL_REQUESTED = "BACKCHANNEL_REQUESTED"
BACKCHANNEL_PLAYED = "BACKCHANNEL_PLAYED"

# ---------------------------------------------------------
# Conversation Intelligence
# ---------------------------------------------------------

EMOTION_UPDATED = "EMOTION_UPDATED"

INTENT_READY = "INTENT_READY"

MEMORY_LOOKUP_STARTED = "MEMORY_LOOKUP_STARTED"
MEMORY_LOOKUP_COMPLETED = "MEMORY_LOOKUP_COMPLETED"

# ---------------------------------------------------------
# Response Events
# ---------------------------------------------------------

RESPONSE_STARTED = "RESPONSE_STARTED"
RESPONSE_STREAM = "RESPONSE_STREAM"
RESPONSE_COMPLETED = "RESPONSE_COMPLETED"

# ---------------------------------------------------------
# Runtime / Validation
# ---------------------------------------------------------

VALIDATION_WARNING = "VALIDATION_WARNING"