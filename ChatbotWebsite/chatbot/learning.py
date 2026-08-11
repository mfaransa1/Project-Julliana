"""Privacy-first helpers for proposing—not automatically accepting—training data."""

from __future__ import annotations

import re
from dataclasses import dataclass

from ChatbotWebsite.chatbot.safety import CrisisDetector


EMAIL_PATTERN = re.compile(r"\b[\w.+-]+@[\w.-]+\.[A-Za-z]{2,}\b")
PHONE_PATTERN = re.compile(r"(?<!\w)(?:\+?\d[\d\s().-]{6,}\d)(?!\w)")
URL_PATTERN = re.compile(r"https?://\S+|www\.\S+", re.IGNORECASE)
WHITESPACE_PATTERN = re.compile(r"\s+")


@dataclass(frozen=True)
class CandidateProposal:
    anonymized_text: str
    proposed_intent: str | None
    confidence: float | None


def propose_candidate(
    message: str,
    *,
    proposed_intent: str | None,
    confidence: float | None,
    threshold: float,
) -> CandidateProposal | None:
    """Return a low-confidence, redacted proposal or reject it for safety/privacy."""
    if confidence is not None and confidence >= threshold:
        return None
    if CrisisDetector().check(message.lower()).is_crisis:
        return None

    anonymized = URL_PATTERN.sub("[link]", message)
    anonymized = EMAIL_PATTERN.sub("[email]", anonymized)
    anonymized = PHONE_PATTERN.sub("[phone]", anonymized)
    anonymized = WHITESPACE_PATTERN.sub(" ", anonymized).strip()

    # Do not retain messages that are too short to be meaningful or too long to review.
    if len(anonymized) < 8 or len(anonymized) > 1000:
        return None
    return CandidateProposal(
        anonymized_text=anonymized,
        proposed_intent=proposed_intent,
        confidence=confidence,
    )
