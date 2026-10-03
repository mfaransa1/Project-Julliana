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


def test_pending_financial_question_handles_an_affirmative_answer():
    state = conversation.ConversationState(
        topic="financial_stress",
        pending_question={
            "text": "Is there a deadline coming up?",
            "type": "yes_no",
            "subtype": "deadline",
            "topic": "financial_stress",
            "intent": "Stress Financial",
        },
    )

    reply = conversation.pending_question_response(state, "Yes.")

    assert reply is not None
    assert "deadline" in reply.lower()


def test_pending_financial_question_does_not_assume_a_deadline_after_no():
    state = conversation.ConversationState(
        topic="financial_stress",
        pending_question={
            "type": "yes_no", "subtype": "deadline", "topic": "financial_stress"
        },
    )

    reply = conversation.pending_question_response(state, "Nope!")

    assert reply is not None
    assert "ongoing expenses" in reply.lower()


def test_pending_question_handles_uncertain_and_short_detail_answers():
    state = conversation.ConversationState(
        topic="financial_stress",
        pending_question={"type": "topic_detail", "topic": "financial_stress"},
    )

    assert conversation.pending_question_response(state, "Maybe.") is not None
    assert conversation.pending_question_response(state, "I don't know.") is not None
    assert conversation.pending_question_response(state, "Rent.") is not None


def test_yes_without_a_pending_question_is_not_a_contextual_answer():
    assert conversation.pending_question_response(
        conversation.ConversationState(), "Yes."
    ) is None


def test_new_topic_signal_is_not_consumed_as_a_short_pending_answer():
    state = conversation.ConversationState(
        pending_question={
            "text": "What part feels difficult?",
            "type": "topic_detail",
            "topic": "general",
        }
    )

    assert conversation.pending_question_response(
        state, "I am worried about money", starts_new_topic=True
    ) is None


def test_pending_metadata_uses_the_exact_question_rendered_in_the_response():
    state = conversation.ConversationState(topic="financial_stress")
    response = (
        "Money worries can feel urgent.\n\n"
        "Do you have anyone safe to talk through the numbers with?"
    )

    conversation.record_pending_question(
        state, response, topic="financial_stress", intent="Stress Financial"
    )

    assert state.pending_question is not None
    assert state.pending_question["text"] == "Do you have anyone safe to talk through the numbers with?"
    assert state.pending_question["type"] == "yes_no"
    assert state.pending_question["subtype"] == "support_contact"
    reply = conversation.pending_question_response(state, "yes")
    assert reply is not None
    assert "deadline" not in reply.lower()
    assert "reach out" in reply.lower()


def test_pending_question_is_replaced_or_cleared_from_the_latest_response():
    state = conversation.ConversationState(
        pending_question={"text": "Is there a deadline coming up?", "subtype": "deadline"}
    )

    conversation.record_pending_question(
        state,
        "Do you have anyone safe to talk through the numbers with?",
        topic="financial_stress",
        intent="Stress Financial",
    )
    assert state.pending_question is not None
    assert state.pending_question["text"] == "Do you have anyone safe to talk through the numbers with?"

    conversation.record_pending_question(
        state, "Take one small step today.", topic="financial_stress", intent="Stress Financial"
    )
    assert state.pending_question is None
    assert state.last_question is None


def test_short_expense_answer_uses_the_expense_question_context():
    state = conversation.ConversationState(
        pending_question={
            "text": "What kind of expense is worrying you?",
            "type": "topic_detail",
            "subtype": "expense",
            "topic": "financial_stress",
        }
    )

    reply = conversation.pending_question_response(state, "Rent")

    assert reply is not None
    assert "expense" in reply.lower()


def test_rent_after_a_general_financial_question_moves_the_conversation_forward():
    state = conversation.ConversationState(
        pending_question={
            "text": "What part of that feels most difficult right now?",
            "type": "topic_detail",
            "topic": "financial_stress",
        }
    )

    reply = conversation.pending_question_response(state, "Rent")

    assert reply is not None
    assert "payment deadline" in reply.lower()


def test_follow_up_path_ends_after_two_clarifying_questions():
    state = conversation.ConversationState(
        follow_up_count=2,
        pending_question={
            "text": "Is there a payment deadline coming up?",
            "type": "yes_no",
            "subtype": "deadline",
            "topic": "financial_stress",
        },
    )

    reply = conversation.pending_question_response(state, "Yes")

    assert reply is not None
    assert "lot to carry" in reply.lower()
    assert "?" not in reply
    conversation.record_pending_question(
        state, reply, topic="financial_stress", intent="Stress Financial"
    )
    assert state.pending_question is None
    assert state.follow_up_count == 0


def test_regular_cost_ends_the_financial_follow_up_without_repeating_a_question():
    state = conversation.ConversationState(
        pending_question={
            "text": "Is there a payment deadline coming up, or is it more about keeping up with the regular cost?",
            "type": "yes_no",
            "subtype": "deadline",
            "topic": "financial_stress",
        }
    )

    reply = conversation.pending_question_response(state, "regular cost")

    assert reply is not None
    assert "lot to carry" in reply.lower()
    assert "?" not in reply


def test_explicit_topic_switch_can_clear_an_old_pending_question():
    state = conversation.ConversationState(
        follow_up_count=1,
        pending_question={"text": "Is there a deadline coming up?"},
    )

    assert conversation.is_explicit_topic_switch("I am sick") is True
    conversation.clear_pending_question(state)

    assert state.pending_question is None
    assert state.follow_up_count == 0
