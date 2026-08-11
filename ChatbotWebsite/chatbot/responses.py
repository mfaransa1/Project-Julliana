"""Intent response selection and bounded in-memory conversation context."""

from __future__ import annotations

import json
import random
from dataclasses import dataclass
from pathlib import Path

from ChatbotWebsite.chatbot.classifier import IntentPrediction
from ChatbotWebsite.chatbot.paths import INTENTS_PATH


FALLBACK_RESPONSE = (
    "I'm not completely sure I understood. Could you explain that another way? "
    "I can offer general support, but I am not a therapist or a substitute for urgent help."
)


@dataclass(frozen=True)
class IntentDefinition:
    tag: str
    responses: tuple[str, ...]
    context_set: str | None = None


class ResponseSelector:
    def __init__(self, intents_path: Path = INTENTS_PATH) -> None:
        self._intents = self._load_intents(intents_path)
        self._context_by_conversation: dict[str, str] = {}

    @staticmethod
    def _load_intents(intents_path: Path) -> dict[str, IntentDefinition]:
        with intents_path.open(encoding="utf-8") as intent_file:
            raw_intents = json.load(intent_file)["intents"]
        return {
            intent["tag"]: IntentDefinition(
                tag=intent["tag"],
                responses=tuple(intent["responses"]),
                context_set=intent.get("context_set") or None,
            )
            for intent in raw_intents
        }

    def choose(
        self, predictions: list[IntentPrediction], conversation_id: str
    ) -> str:
        for prediction in predictions:
            intent = self._intents.get(prediction.tag)
            if intent is None:
                continue
            if intent.tag.lower() == "reiterate":
                contextual = self._contextual_response(conversation_id)
                if contextual:
                    return contextual
            if intent.context_set:
                self._context_by_conversation[conversation_id] = intent.context_set
            return random.choice(intent.responses)
        return FALLBACK_RESPONSE

    def _contextual_response(self, conversation_id: str) -> str | None:
        context = self._context_by_conversation.get(conversation_id)
        if not context:
            return None
        for intent in self._intents.values():
            if intent.context_set == context and intent.responses:
                return random.choice(intent.responses)
        return None
