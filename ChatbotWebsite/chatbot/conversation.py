"""Short-lived, privacy-minimised context for a single chat session."""

from __future__ import annotations

from ChatbotWebsite.chatbot.context import ConversationState


FOLLOW_UP_PHRASES = {
    "is that all",
    "anything else",
    "what else",
    "tell me more",
    "can you explain more",
}
YES_WORDS = {"yes", "yeah", "yep", "ndio", "ee"}
NO_WORDS = {"no", "nope", "hapana", "la"}
AFFIRMATIVE_WORDS = YES_WORDS | {"yup", "sure", "definitely", "of course"}
NEGATIVE_WORDS = NO_WORDS | {"nah", "not really"}
UNCERTAIN_WORDS = {"maybe", "sometimes", "i don't know", "i dont know", "not sure"}
PARTIAL_WORDS = {"a little", "kind of", "somewhat", "occasionally"}
MAX_FOLLOW_UP_QUESTIONS = 2
TOPIC_SWITCH_PHRASES = {
    "i am sick", "i feel sick", "i am ill", "i feel ill", "i am unwell", "i feel unwell",
}


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
        response_context: str | None = None,
    ) -> None:
        state = self.state_for(conversation_id)
        intent_changed = bool(intent and intent != state.intent)
        if intent_changed:
            state.context_bridge_used = False
        state.intent = intent
        if intent_changed:
            state.topic = topic_for_intent(intent) or state.topic
        state.emotion = emotion
        state.language = language
        record_pending_question(state, response, topic=state.topic, intent=intent)
        state.response_context = response_context
        state.touch()

    def mark_context_bridge_used(self, conversation_id: str) -> None:
        """Permit at most one inferred short-answer bridge per active topic."""
        self.state_for(conversation_id).context_bridge_used = True

    def start_safety_check(self, conversation_id: str) -> None:
        state = self.state_for(conversation_id)
        state.safety_check_pending = True
        state.awaiting_question = True
        state.touch()

    def resolve_safety_check(self, conversation_id: str) -> None:
        state = self.state_for(conversation_id)
        state.safety_check_pending = False
        state.touch()


def normalized_phrase(message: str) -> str:
    return " ".join(message.casefold().strip(" .!?").split())


def is_follow_up_request(message: str) -> bool:
    return normalized_phrase(message) in FOLLOW_UP_PHRASES


def yes_or_no(message: str) -> bool | None:
    phrase = normalized_phrase(message)
    if phrase in AFFIRMATIVE_WORDS:
        return True
    if phrase in NEGATIVE_WORDS:
        return False
    return None


def answer_type(message: str) -> str | None:
    """Classify only compact replies that can answer a pending bot question."""
    phrase = normalized_phrase(message)
    if phrase in AFFIRMATIVE_WORDS:
        return "affirmative"
    if phrase in NEGATIVE_WORDS:
        return "negative"
    if phrase in UNCERTAIN_WORDS:
        return "uncertain"
    if phrase in PARTIAL_WORDS:
        return "partial"
    if 1 <= len(phrase.split()) <= 6:
        return "topic_detail"
    return None


def pending_question_for_response(
    response: str, *, topic: str | None, intent: str | None
) -> dict[str, str] | None:
    """Keep structured metadata for the latest bot question, never user text."""
    question = next(
        (line.strip() for line in reversed(response.splitlines()) if line.strip().endswith("?")),
        None,
    )
    if not question:
        return None
    lower_question = question.casefold()
    subtype = ""
    if any(term in lower_question for term in ("deadline", "due date", "due this")):
        question_type = "yes_no" if lower_question.startswith(("is ", "are ", "do ", "does ", "have ", "has ", "can ", "did ", "will ")) else "deadline"
        subtype = "deadline"
    elif any(term in lower_question for term in ("anyone safe", "someone safe", "talk through", "reach out")):
        question_type = "yes_no" if lower_question.startswith(("is ", "are ", "do ", "does ", "have ", "has ", "can ", "did ", "will ")) else "topic_detail"
        subtype = "support_contact"
    elif any(term in lower_question for term in ("expense", "rent", "bill", "debt")):
        question_type = "topic_detail"
        subtype = "expense"
    elif any(term in lower_question for term in ("how long", "when did", "several nights")):
        question_type = "timeframe"
    elif any(term in lower_question for term in ("how much", "amount", "cost")):
        question_type = "amount"
    elif lower_question.startswith(("is ", "are ", "do ", "does ", "have ", "has ", "can ", "did ", "will ")):
        question_type = "yes_no"
    elif " or " in lower_question:
        question_type = "choice"
    elif any(term in lower_question for term in ("feel", "feeling", "emotion")):
        question_type = "emotion"
    else:
        question_type = "topic_detail"
    return {
        "text": question,
        "type": question_type,
        "topic": topic or "general",
        "intent": intent or "",
        "subtype": subtype,
    }


def record_pending_question(
    state: ConversationState, response: str, *, topic: str | None, intent: str | None
) -> None:
    """Replace pending metadata from the exact final response sent to the user."""
    pending_question = pending_question_for_response(
        response, topic=topic, intent=intent
    )
    state.awaiting_question = pending_question is not None
    state.last_question = pending_question["text"] if pending_question else None
    state.pending_question = pending_question
    state.follow_up_count = state.follow_up_count + 1 if pending_question else 0


def clear_pending_question(state: ConversationState) -> None:
    """End the current focused follow-up path without retaining stale metadata."""
    state.awaiting_question = False
    state.last_question = None
    state.pending_question = None
    state.follow_up_count = 0


def is_explicit_topic_switch(message: str) -> bool:
    """Recognise a small set of clear topic changes not yet in the knowledge catalog."""
    return normalized_phrase(message) in TOPIC_SWITCH_PHRASES


def closing_response(topic: str) -> str:
    """End a bounded clarification sequence with a useful, non-interrogating reply."""
    closings = {
        "financial_stress": (
            "That sounds like a lot to carry. If you can, write down the amount and due date, "
            "then contact the landlord, provider, or someone you trust early to ask what options are available."
        ),
        "exam_anxiety": (
            "You have identified an important pressure point. Choose one small revision task, take a short break, "
            "and return when you are ready rather than trying to solve the whole exam at once."
        ),
        "sleep_reset": (
            "A gentle wind-down and a consistent wake-up time can be a useful place to start. If sleep stays severely "
            "difficult or worsens, consider speaking with a clinician."
        ),
    }
    return closings.get(
        topic,
        "Thanks for sharing that. Take the next small step that feels manageable, and you can return whenever you want to talk more.",
    )


def pending_question_response(
    state: ConversationState, message: str, *, starts_new_topic: bool = False
) -> str | None:
    """Resolve a compact answer before it can be mistaken for an unknown intent."""
    if starts_new_topic or not state.pending_question:
        return None
    kind = answer_type(message)
    if kind is None:
        return None
    topic = state.pending_question.get("topic", "general")
    if state.follow_up_count >= MAX_FOLLOW_UP_QUESTIONS:
        return closing_response(topic)
    subtype = state.pending_question.get("subtype", "")
    if subtype == "support_contact":
        support_replies = {
            "affirmative": "I'm glad there is someone you could talk to. Would it feel possible to reach out to them today?",
            "negative": "That can make money worries feel heavier. Is there one person or local support service you might feel comfortable contacting?",
            "uncertain": "That's okay. Would it help to think of one person who has felt safe to talk to before?",
        }
        if kind in support_replies:
            return support_replies[kind]
    if subtype == "expense" and kind == "topic_detail":
        return "Thanks for explaining. What about that expense feels most difficult right now?"
    if topic == "financial_stress" and kind == "topic_detail":
        phrase = normalized_phrase(message)
        if "regular cost" in phrase or "rent is due" in phrase or "due" in phrase:
            return closing_response(topic)
        return (
            "That sounds like an important expense to carry. Is there a payment "
            "deadline coming up, or is it more about keeping up with the regular cost?"
        )
    specific = {
        "financial_stress": {
            "affirmative": "Okay. What kind of deadline is coming up?",
            "negative": "Okay. Is the money worry more about ongoing expenses, debt, or something else?",
            "uncertain": "That's okay. Which part of the money situation feels most unclear right now?",
        },
        "exam_anxiety": {
            "affirmative": "Okay. What subject or part of the exam feels hardest right now?",
            "negative": "Okay. What has made studying difficult lately?",
        },
        "academic_stress_first_step": {
            "affirmative": "Okay. What part of school feels most urgent right now?",
            "negative": "Okay. What is making school feel difficult at the moment?",
        },
        "sleep_reset": {
            "affirmative": "Okay. Has it been happening for several nights, or did it start recently?",
            "negative": "Okay. What tends to keep you awake when sleep is difficult?",
        },
        "loneliness_connection": {
            "negative": "That can make things feel harder. Is there one low-pressure way to be around people today?",
            "affirmative": "I'm glad there is someone in your life. Would it feel possible to reach out to them?",
        },
    }
    if subtype == "deadline" and kind in specific.get(topic, {}):
        return specific[topic][kind]
    generic = {
        "affirmative": "Okay. Could you tell me a little more about that?",
        "negative": "Okay. What feels closer to the issue for you?",
        "uncertain": "That's okay. What part feels hardest to put into words?",
        "partial": "Thanks for saying that. What happens when it feels strongest?",
        "topic_detail": "Thanks for explaining. What part of that feels most difficult right now?",
    }
    return generic[kind]


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
