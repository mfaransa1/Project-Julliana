"""Crisis-first safety checks independent from the intent classifier."""

from __future__ import annotations

from dataclasses import dataclass


CRISIS_PATTERNS = (
    "suicide",
    "kill myself",
    "end my life",
    "i want to die",
    "life is pointless",
    "i can't go on",
    "nataka kufa",
    "sitaki kuishi",
    "maisha haina maana",
    "nimechoka kuishi",
    "nataka kujitoa",
    "adwaro tho",
    "aonge gi dwaro mar ngima",
    "ngima oonge gi tiend",
    "dwa mar tho omaka",
    "anyalo dhi marach",
)

CRISIS_RESPONSE = (
    "I'm really sorry you're feeling this way. You are not alone.\n"
    "Please reach out immediately:\n"
    "- Call 1199 (Kenya Red Cross emergency support)\n"
    "- Talk to someone you trust\n"
    "- Visit a nearby hospital"
)


@dataclass(frozen=True)
class SafetyResult:
    is_crisis: bool
    matched_pattern: str | None = None


class CrisisDetector:
    """A deliberately isolated, conservative first-line crisis detector."""

    def check(self, normalized_message: str) -> SafetyResult:
        normalized_message = " ".join(normalized_message.lower().split())
        for pattern in CRISIS_PATTERNS:
            if pattern in normalized_message:
                return SafetyResult(is_crisis=True, matched_pattern=pattern)
        return SafetyResult(is_crisis=False)


def is_crisis(message: str) -> bool:
    """Compatibility helper for callers outside the engine."""
    return CrisisDetector().check(message.lower()).is_crisis
