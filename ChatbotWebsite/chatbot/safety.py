"""Crisis-first safety checks independent from the intent classifier."""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum


class SafetyLevel(StrEnum):
    NONE = "none"
    LOW_CONCERN = "low_concern"
    ELEVATED_CONCERN = "elevated_concern"
    HIGH_CONCERN = "high_concern"
    IMMEDIATE_CRISIS = "immediate_crisis"


IMMEDIATE_PATTERNS = (
    "kill myself",
    "end my life",
    "i want to die",
    "i don't want to be alive",
    "i do not want to be alive",
    "i want to hurt myself",
    "i am going to hurt myself",
    "kill my self",
    "hurt my self",
    "end it all",
    "i want to kms",
    "i am suicidal",
    "suicide",
    "nataka kujitoa",
    "life is pointless",
    "nataka kufa",
    "sitaki kuishi",
    "maisha haina maana",
    "nimechoka kuishi",
    "adwaro tho",
    "aonge gi dwaro mar ngima",
    "ngima oonge gi tiend",
    "dwa mar tho omaka",
    "anyalo dhi marach",
)

HIGH_CONCERN_PATTERNS = (
    "everyone would be better without me",
    "i can't keep going",
    "i cannot keep going",
    "there is no point anymore",
    "there's no point anymore",
    "i have no reason to live",
)

# These common idioms are upsetting but do not by themselves signal self-harm.
NON_CRISIS_IDIOMS = (
    "this exam is killing me",
    "i could die from this exam",
    "dying of embarrassment",
)

CRISIS_RESPONSE = (
    "I'm really sorry you're feeling this way. You are not alone.\n"
    "Please seek immediate real-world support:\n"
    "- Contact local emergency services or go to the nearest emergency department\n"
    "- Tell someone you trust and, if you can, stay with them\n"
    "- Use Juliana's Get urgent help page to find the current support directory"
)


@dataclass(frozen=True)
class SafetyResult:
    level: SafetyLevel = SafetyLevel.NONE
    matched_pattern: str | None = None

    @property
    def is_crisis(self) -> bool:
        return self.level in {SafetyLevel.HIGH_CONCERN, SafetyLevel.IMMEDIATE_CRISIS}


class CrisisDetector:
    """A deliberately isolated, conservative first-line crisis detector."""

    def check(self, normalized_message: str) -> SafetyResult:
        normalized_message = " ".join(normalized_message.lower().split())
        if any(idiom in normalized_message for idiom in NON_CRISIS_IDIOMS):
            return SafetyResult()
        for pattern in IMMEDIATE_PATTERNS:
            if pattern in normalized_message:
                return SafetyResult(
                    level=SafetyLevel.IMMEDIATE_CRISIS, matched_pattern=pattern
                )
        for pattern in HIGH_CONCERN_PATTERNS:
            if pattern in normalized_message:
                return SafetyResult(level=SafetyLevel.HIGH_CONCERN, matched_pattern=pattern)
        return SafetyResult()


def is_crisis(message: str) -> bool:
    """Compatibility helper for callers outside the engine."""
    return CrisisDetector().check(message.lower()).is_crisis
