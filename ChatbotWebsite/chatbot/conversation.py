"""Short-lived, privacy-minimised context for a single chat session."""

from __future__ import annotations

from dataclasses import dataclass


FOLLOW_UP_PHRASES = {
    "is that all",
    "anything else",
    "what else",
    "tell me more",
    "can you explain more",
}
YES_WORDS = {"yes", "yeah", "yep", "ndio", "ee"}
NO_WORDS = {"no", "nope", "hapana", "la"}


@dataclass
class ConversationState:
    """Only operational context; never persisted as a user profile."""

    topic: str | None = None
    intent: str | None = None
    emotion: str | None = None
    language: str | None = None
    awaiting_question: bool = False
    safety_check_pending: bool = False
    last_response: str | None = None
    context_bridge_used: bool = False


class ConversationMemory:
    """Process-local state with no raw-message retention or database writes."""

    def __init__(self) -> None:
        self._states: dict[str, ConversationState] = {}

    def state_for(self, conversation_id: str) -> ConversationState:
        return self._states.setdefault(conversation_id, ConversationState())

    def remember(
        self,
        conversation_id: str,
        *,
        intent: str | None,
        emotion: str,
        language: str,
        response: str,
    ) -> None:
        state = self.state_for(conversation_id)
        if intent and intent != state.intent:
            state.context_bridge_used = False
        state.intent = intent
        state.topic = topic_for_intent(intent) or state.topic
        state.emotion = emotion
        state.language = language
        state.awaiting_question = response.rstrip().endswith("?")
        state.last_response = response

    def mark_context_bridge_used(self, conversation_id: str) -> None:
        """Permit at most one inferred short-answer bridge per active topic."""
        self.state_for(conversation_id).context_bridge_used = True

    def start_safety_check(self, conversation_id: str) -> None:
        state = self.state_for(conversation_id)
        state.safety_check_pending = True
        state.awaiting_question = True

    def resolve_safety_check(self, conversation_id: str) -> None:
        self.state_for(conversation_id).safety_check_pending = False


def normalized_phrase(message: str) -> str:
    return " ".join(message.casefold().strip(" .!?").split())


def is_follow_up_request(message: str) -> bool:
    return normalized_phrase(message) in FOLLOW_UP_PHRASES


def yes_or_no(message: str) -> bool | None:
    phrase = normalized_phrase(message)
    if phrase in YES_WORDS:
        return True
    if phrase in NO_WORDS:
        return False
    return None


def topic_for_intent(intent: str | None) -> str | None:
    if not intent:
        return None
    normalized = intent.casefold()
    for topic in ("stress", "anxiety", "sad", "lonely", "grief", "sleep", "trauma"):
        if topic in normalized:
            return topic
    return None


def follow_up_response(state: ConversationState, message: str) -> str | None:
    """Handle explicit continuity requests without guessing a new intent."""
    if not state.topic or not is_follow_up_request(message):
        return None
    prompts = {
        "stress": "There can be more to it than one quick tip. What has been the hardest part of the stress lately—school, work, relationships, or something else?",
        "anxiety": "We can take this one step at a time. What tends to make the anxious feeling strongest for you?",
        "sad": "I'm glad you told me. Would you like to share what has been making things feel heavy?",
        "lonely": "Feeling alone can be difficult. Is there a time of day or situation when it feels strongest?",
        "grief": "Grief can come in waves. Would you like to tell me a little about what you are carrying today?",
        "sleep": "Sleep can be affected by many things. Is it harder to fall asleep, stay asleep, or wake feeling rested?",
        "trauma": "You do not have to share details you are not comfortable sharing. What kind of support would feel most helpful right now?",
    }
    return prompts.get(state.topic, "I'm here with you. What would feel most useful to talk through next?")


def contextual_answer_response(state: ConversationState, message: str) -> str | None:
    """Treat a likely short answer as context only under narrow conditions."""
    words = normalized_phrase(message).split()
    if (
        not state.topic
        or state.context_bridge_used
        or yes_or_no(message) is not None
        or not 1 <= len(words) <= 6
    ):
        return None
    stress_anchor = bool(set(words) & {"school", "exam", "exams", "work", "family", "relationship"})
    if not state.awaiting_question and not (state.topic == "stress" and stress_anchor):
        return None
    if state.topic == "sad" and set(words) & {"sick", "ill", "unwell"}:
        return (
            "I'm sorry you are feeling unwell. Physical illness can make emotions feel "
            "heavier too. Rest and fluids may help, and please consider a clinician if "
            "your symptoms are severe, worsening, or worrying."
        )
    prompts = {
        "stress": "Thanks for sharing that. It sounds as though that may be adding to the stress. What part feels most difficult right now?",
        "anxiety": "Thank you for saying that. What happens in your body or thoughts when that feeling starts?",
        "sad": "Thank you for sharing that with me. Would you like to say a little more about it?",
        "lonely": "That sounds hard. Is there someone you would feel comfortable reaching out to, even for a short message?",
        "sleep": "Thanks for explaining. What is your routine like in the hour before bed?",
    }
    return prompts.get(state.topic)
