"""Safety-first orchestration for Project Juliana's local intent chatbot."""

from __future__ import annotations

from dataclasses import dataclass

from ChatbotWebsite.chatbot.classifier import IntentClassifier
from ChatbotWebsite.chatbot.emotion import EmotionAnalyzer
from ChatbotWebsite.chatbot.language import MessageNormalizer
from ChatbotWebsite.chatbot.model_manager import ModelUnavailable
from ChatbotWebsite.chatbot.responses import FALLBACK_RESPONSE, ResponseSelector
from ChatbotWebsite.chatbot.safety import CRISIS_RESPONSE, CrisisDetector


NEGATIVE_EMOTION_RESPONSE = (
    "It sounds like you may be feeling very low. I'm here to listen if you'd like "
    "to share more about what is weighing on you."
)


class ChatbotEngine:
    """Keep safety, language, classification, and response selection independent."""

    def __init__(self) -> None:
        self._normalizer = MessageNormalizer()
        self._safety = CrisisDetector()
        self._emotion = EmotionAnalyzer()
        self._classifier = IntentClassifier(normalizer=self._normalizer)
        self._responses = ResponseSelector()

    def reply(self, message: str, conversation_id: str) -> str:
        return self.reply_with_metadata(message, conversation_id).text

    def reply_with_metadata(self, message: str, conversation_id: str) -> "ChatbotReply":
        normalized = self._normalizer.normalize_for_safety(message)
        language = self._normalizer.detect_language(message)
        if self._safety.check(normalized).is_crisis:
            return ChatbotReply(
                text=CRISIS_RESPONSE, language=language.code, learning_eligible=False
            )

        if self._emotion.detect(message) == "negative":
            return ChatbotReply(
                text=NEGATIVE_EMOTION_RESPONSE, language=language.code, learning_eligible=False
            )

        try:
            predictions = self._classifier.predict(message)
        except ModelUnavailable:
            return ChatbotReply(
                text=FALLBACK_RESPONSE, language=language.code, learning_eligible=False
            )
        top_prediction = predictions[0] if predictions else None
        return ChatbotReply(
            text=self._responses.choose(predictions, conversation_id),
            proposed_intent=top_prediction.tag if top_prediction else None,
            confidence=top_prediction.confidence if top_prediction else None,
            language=language.code,
            learning_eligible=True,
        )


@dataclass(frozen=True)
class ChatbotReply:
    text: str
    proposed_intent: str | None = None
    confidence: float | None = None
    language: str | None = None
    learning_eligible: bool = False


_engine: ChatbotEngine | None = None


def get_engine() -> ChatbotEngine:
    global _engine
    if _engine is None:
        _engine = ChatbotEngine()
    return _engine


def get_response(message: str, conversation_id: str = "guest") -> str:
    """Compatibility entry point used by the Flask routes."""
    return get_engine().reply(message, conversation_id)


def get_reply(message: str, conversation_id: str = "guest") -> ChatbotReply:
    """Return a response plus non-sensitive classifier metadata for review flow."""
    return get_engine().reply_with_metadata(message, conversation_id)
