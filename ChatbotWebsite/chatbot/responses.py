"""Intent response selection using caller-owned conversation context."""

from __future__ import annotations

import json
import random
from dataclasses import dataclass
from pathlib import Path

from ChatbotWebsite.chatbot.classifier import IntentPrediction
from ChatbotWebsite.chatbot.knowledge import KnowledgeEntry
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
        self, predictions: list[IntentPrediction], active_context: str | None = None
    ) -> str:
        for prediction in predictions:
            intent = self._intents.get(prediction.tag)
            if intent is None:
                continue
            if intent.tag.lower() == "reiterate":
                contextual = self._contextual_response(active_context)
                if contextual:
                    return contextual
            return random.choice(intent.responses)
        return FALLBACK_RESPONSE

    def context_for(self, predictions: list[IntentPrediction]) -> str | None:
        """Return the curated context label selected by the current intent."""
        for prediction in predictions:
            intent = self._intents.get(prediction.tag)
            if intent and intent.tag.lower() != "reiterate":
                return intent.context_set
        return None

    @staticmethod
    def compose_knowledge(entry: KnowledgeEntry) -> str:
        """Build a compact reply solely from reviewed knowledge entry material."""
        parts = [entry.response]
        if entry.knowledge:
            parts.append(random.choice(entry.knowledge))
        if entry.actions:
            parts.append(f"One small thing to try: {random.choice(entry.actions)}")
        if entry.questions:
            parts.append(random.choice(entry.questions))
        return "\n\n".join(parts)

    def _contextual_response(self, context: str | None) -> str | None:
        if not context:
            return None
        for intent in self._intents.values():
            if intent.context_set == context and intent.responses:
                return random.choice(intent.responses)
        return None
