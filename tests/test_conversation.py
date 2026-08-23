import importlib.util
import sys
from pathlib import Path


CONVERSATION_PATH = (
    Path(__file__).resolve().parents[1]
    / "ChatbotWebsite"
    / "chatbot"
    / "conversation.py"
)
spec = importlib.util.spec_from_file_location("juliana_conversation", CONVERSATION_PATH)
assert spec and spec.loader
conversation = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = conversation
spec.loader.exec_module(conversation)


def test_follow_up_request_keeps_the_active_stress_topic():
    memory = conversation.ConversationMemory()
    memory.remember(
        "guest:example",
        intent="Stressed Feeling",
        emotion="negative",
        language="en",
        response="What has been difficult lately?",
    )

    reply = conversation.follow_up_response(
        memory.state_for("guest:example"), "Is that all?"
    )

    assert reply is not None
    assert "stress" in reply.lower()


def test_safety_yes_no_recognises_english_and_kiswahili():
    assert conversation.yes_or_no("yes") is True
    assert conversation.yes_or_no("hapana") is False
    assert conversation.yes_or_no("maybe") is None


def test_short_answer_continues_an_open_stress_question():
    state = conversation.ConversationState(topic="stress", awaiting_question=True)

    reply = conversation.contextual_answer_response(state, "School exams")

    assert reply is not None
    assert "stress" in reply.lower()


def test_contextual_bridge_does_not_repeat_for_yes_or_multiple_short_answers():
    state = conversation.ConversationState(topic="sad", awaiting_question=True)

    assert conversation.contextual_answer_response(state, "I am sick") is not None
    state.context_bridge_used = True
    assert conversation.contextual_answer_response(state, "Yes") is None
    assert conversation.contextual_answer_response(state, "I feel depressed") is None
