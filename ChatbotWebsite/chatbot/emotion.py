"""Non-clinical linguistic sentiment signals for response selection."""

from __future__ import annotations

from nltk.sentiment import SentimentIntensityAnalyzer


class EmotionAnalyzer:
    """Expose only linguistic signals, never a diagnosis."""

    def __init__(self) -> None:
        self._analyzer: SentimentIntensityAnalyzer | None = None

    def detect(self, message: str) -> str:
        try:
            if self._analyzer is None:
                self._analyzer = SentimentIntensityAnalyzer()
            score = self._analyzer.polarity_scores(message)["compound"]
        except LookupError:
            return "neutral"

        if score >= 0.5:
            return "positive"
        if score <= -0.5:
            return "negative"
        return "neutral"


def detect_emotion(message: str) -> str:
    """Compatibility helper for callers outside the engine."""
    return EmotionAnalyzer().detect(message)
