"""Minimal, session-scoped operational context for a Juliana conversation.

This module deliberately stores no user message text.  The browser session keeps
only the small amount of state needed to connect the next turn to the last one.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, fields
from datetime import datetime, timezone
from typing import Any, Mapping


@dataclass
class ConversationState:
    """Non-sensitive signals used to resolve a single active conversation."""

    topic: str | None = None
    intent: str | None = None
    emotion: str | None = None
    language: str | None = None
    response_context: str | None = None
    last_question: str | None = None
    pending_question: dict[str, str] | None = None
    follow_up_count: int = 0
    awaiting_question: bool = False
    safety_check_pending: bool = False
    context_bridge_used: bool = False
    updated_at: str | None = None

    def touch(self) -> None:
        self.updated_at = datetime.now(timezone.utc).isoformat()


_STATE_FIELDS = {field.name for field in fields(ConversationState)}


def state_from_session(raw_state: Mapping[str, Any] | None) -> ConversationState:
    """Read only recognised state fields from a signed Flask session payload."""
    if not isinstance(raw_state, Mapping):
        return ConversationState()
    return ConversationState(**{key: value for key, value in raw_state.items() if key in _STATE_FIELDS})


def state_for_session(state: ConversationState) -> dict[str, Any]:
    """Serialize the minimal context state; raw messages are never included."""
    return asdict(state)
