from ChatbotWebsite.chatbot.context import ConversationState, state_for_session, state_from_session
from ChatbotWebsite.chatbot.knowledge import KnowledgeRetriever


def test_session_context_contains_operational_signals_not_raw_messages():
    state = ConversationState(topic="stress", intent="Stress School", emotion="negative")

    payload = state_for_session(state)

    assert payload["topic"] == "stress"
    assert "message" not in payload
    assert state_from_session({"topic": "sleep", "message": "private text"}).topic == "sleep"


def test_curated_knowledge_retrieves_an_academic_stress_entry():
    entry = KnowledgeRetriever().retrieve("My exams are overwhelming", "Stress School")

    assert entry is not None
    assert entry.id == "academic-stress-first-step"
    assert entry.actions
    assert entry.questions


def test_phrase_matching_handles_natural_language_not_just_a_single_keyword():
    entry = KnowledgeRetriever().retrieve("I keep putting things off")

    assert entry is not None
    assert entry.id == "procrastination"
    assert KnowledgeRetriever().has_phrase_match(entry, "I keep putting things off")
