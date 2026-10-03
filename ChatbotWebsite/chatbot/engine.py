"""Safety-first orchestration for Project Juliana's local intent chatbot."""

from __future__ import annotations

import logging
from dataclasses import dataclass

from ChatbotWebsite.chatbot.classifier import IntentClassifier
from ChatbotWebsite.chatbot.conversation import (
    contextual_answer_response,
    clear_pending_question,
    follow_up_response,
    is_explicit_topic_switch,
    pending_question_response,
    record_pending_question,
    topic_for_intent,
    yes_or_no,
)
from ChatbotWebsite.chatbot.context import ConversationState
from ChatbotWebsite.chatbot.emotion import EmotionAnalyzer
from ChatbotWebsite.chatbot.language import MessageNormalizer
from ChatbotWebsite.chatbot.knowledge import KnowledgeRetriever
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
        self._knowledge = KnowledgeRetriever()

    def reply(self, message: str, conversation_id: str) -> str:
        return self.reply_with_metadata(message, conversation_id).text

    def reply_with_metadata(self, message: str, conversation_id: str) -> "ChatbotReply":
        """Compatibility wrapper for non-web callers without saved context."""
        return self.reply_in_context(message, ConversationState())

    def reply_in_context(
        self, message: str, state: ConversationState
    ) -> "ChatbotReply":
        """Process a turn using caller-owned, minimal conversation state."""
        normalized = self._normalizer.normalize_for_safety(message)
        language = self._normalizer.detect_language(message)
        safety = self._safety.check(normalized)
        safety_follow_up = yes_or_no(message) if state.safety_check_pending else None
        if safety_follow_up is not None:
            state.safety_check_pending = False
            state.touch()
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
            state.safety_check_pending = True
            state.awaiting_question = True
            state.last_question = None
            state.pending_question = None
            state.touch()
            return ChatbotReply(
                text=f"{CRISIS_RESPONSE}\n\nAre you in immediate danger of hurting yourself right now?",
                language=language.code,
                learning_eligible=False,
                safety_level=safety.level,
            )

        candidate_knowledge = self._knowledge.retrieve(
            message, state.intent, state.topic
        )
        starts_new_topic = bool(
            candidate_knowledge
            and self._knowledge.has_phrase_match(candidate_knowledge, message)
        )
        if starts_new_topic or is_explicit_topic_switch(message):
            clear_pending_question(state)
        contextual = pending_question_response(
            state, message, starts_new_topic=starts_new_topic
        )
        contextual = contextual or follow_up_response(state, message)
        contextual = contextual or contextual_answer_response(state, message)
        if contextual:
            state.context_bridge_used = True
            self._remember(
                state,
                intent=state.intent,
                emotion=state.emotion or "neutral",
                language=language.code,
                response=contextual,
                response_context=state.response_context,
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
        response = self._responses.choose(predictions, state.response_context)
        knowledge = self._knowledge.retrieve(
            message, top_prediction.tag if top_prediction else None, state.topic
        )
        used_knowledge = knowledge and (
            response == FALLBACK_RESPONSE
            or self._knowledge.has_phrase_match(knowledge, message)
        )
        if used_knowledge:
            response = self._responses.compose_knowledge(knowledge)
        if response == FALLBACK_RESPONSE and emotion == "negative":
            response = NEGATIVE_EMOTION_RESPONSE
        self._remember(
            state,
            intent=top_prediction.tag if top_prediction else None,
            emotion=emotion,
            language=language.code,
            response=response,
            response_context=self._responses.context_for(predictions),
            topic=knowledge.id.replace("-", "_") if used_knowledge else None,
        )
        return ChatbotReply(
            text=response,
            proposed_intent=top_prediction.tag if top_prediction else None,
            confidence=top_prediction.confidence if top_prediction else None,
            language=language.code,
            learning_eligible=True,
            safety_level=safety.level,
        )

    @staticmethod
    def _remember(
        state: ConversationState,
        *,
        intent: str | None,
        emotion: str,
        language: str,
        response: str,
        response_context: str | None,
        topic: str | None = None,
    ) -> None:
        intent_changed = bool(intent and intent != state.intent)
        if intent_changed:
            state.context_bridge_used = False
        state.intent = intent
        if topic:
            state.topic = topic
        elif intent_changed:
            state.topic = topic_for_intent(intent) or state.topic
        state.emotion = emotion
        state.language = language
        state.response_context = response_context
        record_pending_question(state, response, topic=state.topic, intent=intent)
        state.touch()


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


def get_reply(
    message: str,
    conversation_id: str = "guest",
    state: ConversationState | None = None,
) -> ChatbotReply:
    """Return a response plus non-sensitive classifier metadata for review flow."""
    if state is None:
        return get_engine().reply_with_metadata(message, conversation_id)
    return get_engine().reply_in_context(message, state)
