"""Safety-first orchestration for Project Juliana's local intent chatbot."""

from __future__ import annotations

import logging
from dataclasses import dataclass

from ChatbotWebsite.chatbot.classifier import IntentClassifier
from ChatbotWebsite.chatbot.conversation import (
    ConversationMemory,
    contextual_answer_response,
    follow_up_response,
    yes_or_no,
)
from ChatbotWebsite.chatbot.emotion import EmotionAnalyzer
from ChatbotWebsite.chatbot.language import MessageNormalizer
from ChatbotWebsite.chatbot.model_manager import ModelUnavailable
from ChatbotWebsite.chatbot.responses import FALLBACK_RESPONSE, ResponseSelector
from ChatbotWebsite.chatbot.safety import CRISIS_RESPONSE, CrisisDetector, SafetyLevel


NEGATIVE_EMOTION_RESPONSE = (
    "It sounds like you may be feeling very low. I'm here to listen if you'd like "
    "to share more about what is weighing on you."
)
logger = logging.getLogger(__name__)


class ChatbotEngine:
    """Keep safety, language, classification, and response selection independent."""

    def __init__(self) -> None:
        self._normalizer = MessageNormalizer()
        self._safety = CrisisDetector()
        self._emotion = EmotionAnalyzer()
        self._classifier = IntentClassifier(normalizer=self._normalizer)
        self._responses = ResponseSelector()
        self._memory = ConversationMemory()

    def reply(self, message: str, conversation_id: str) -> str:
        return self.reply_with_metadata(message, conversation_id).text

    def reply_with_metadata(self, message: str, conversation_id: str) -> "ChatbotReply":
        normalized = self._normalizer.normalize_for_safety(message)
        language = self._normalizer.detect_language(message)
        state = self._memory.state_for(conversation_id)
        safety = self._safety.check(normalized)
        safety_follow_up = yes_or_no(message) if state.safety_check_pending else None
        if safety_follow_up is not None:
            self._memory.resolve_safety_check(conversation_id)
            if safety_follow_up:
                return ChatbotReply(
                    text=CRISIS_RESPONSE,
                    language=language.code,
                    learning_eligible=False,
                    safety_level=SafetyLevel.IMMEDIATE_CRISIS,
                )
            return ChatbotReply(
                text="Thank you for telling me. Even if you are not in immediate danger, you deserve support. Could you reach out to someone you trust today, and stay with them if the feeling gets stronger?",
                language=language.code,
                learning_eligible=False,
                safety_level=SafetyLevel.HIGH_CONCERN,
            )
        if safety.is_crisis:
            self._memory.start_safety_check(conversation_id)
            return ChatbotReply(
                text=f"{CRISIS_RESPONSE}\n\nAre you in immediate danger of hurting yourself right now?",
                language=language.code,
                learning_eligible=False,
                safety_level=safety.level,
            )

        contextual = follow_up_response(state, message)
        contextual = contextual or contextual_answer_response(state, message)
        if contextual:
            self._memory.mark_context_bridge_used(conversation_id)
            self._memory.remember(
                conversation_id,
                intent=state.intent,
                emotion=state.emotion or "neutral",
                language=language.code,
                response=contextual,
            )
            return ChatbotReply(
                text=contextual,
                proposed_intent=state.intent,
                language=language.code,
                learning_eligible=False,
            )

        emotion = self._emotion.detect(message)

        try:
            predictions = self._classifier.predict(message)
        except ModelUnavailable:
            # Intentionally exclude the message: it may contain sensitive content.
            logger.warning("Chatbot model is unavailable; returning safe fallback.")
            return ChatbotReply(
                text=(
                    NEGATIVE_EMOTION_RESPONSE
                    if emotion == "negative"
                    else FALLBACK_RESPONSE
                ),
                language=language.code,
                learning_eligible=False,
            )
        top_prediction = predictions[0] if predictions else None
        response = self._responses.choose(predictions, conversation_id)
        if response == FALLBACK_RESPONSE and emotion == "negative":
            response = NEGATIVE_EMOTION_RESPONSE
        self._memory.remember(
            conversation_id,
            intent=top_prediction.tag if top_prediction else None,
            emotion=emotion,
            language=language.code,
            response=response,
        )
        return ChatbotReply(
            text=response,
            proposed_intent=top_prediction.tag if top_prediction else None,
            confidence=top_prediction.confidence if top_prediction else None,
            language=language.code,
            learning_eligible=True,
            safety_level=safety.level,
        )


@dataclass(frozen=True)
class ChatbotReply:
    text: str
    proposed_intent: str | None = None
    confidence: float | None = None
    language: str | None = None
    learning_eligible: bool = False
    safety_level: SafetyLevel = SafetyLevel.NONE


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
