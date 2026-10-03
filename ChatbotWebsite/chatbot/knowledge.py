"""Small, curated retrieval layer for safe, non-generative wellbeing guidance."""

from __future__ import annotations

import json
import re
from dataclasses import dataclass
from pathlib import Path

from ChatbotWebsite.chatbot.paths import KNOWLEDGE_PATH


@dataclass(frozen=True)
class KnowledgeEntry:
    id: str
    name: str
    keywords: tuple[str, ...]
    phrases: tuple[str, ...]
    intents: tuple[str, ...]
    response: str
    knowledge: tuple[str, ...]
    actions: tuple[str, ...]
    questions: tuple[str, ...]
    related_topics: tuple[str, ...]
    combinations: tuple[str, ...]


class KnowledgeRetriever:
    """Retrieve only reviewed content; it never searches the web or generates text."""

    def __init__(self, path: Path = KNOWLEDGE_PATH) -> None:
        self._entries = self._load(path)

    @staticmethod
    def _load(path: Path) -> tuple[KnowledgeEntry, ...]:
        try:
            with path.open(encoding="utf-8") as knowledge_file:
                entries = json.load(knowledge_file).get("entries", [])
        except (OSError, json.JSONDecodeError):
            return ()
        return tuple(
            KnowledgeEntry(
                id=entry["id"],
                name=entry.get("name", entry["id"]),
                keywords=tuple(entry.get("keywords", ())),
                phrases=tuple(entry.get("phrases", ())),
                intents=tuple(entry.get("intents", ())),
                response=entry["response"],
                knowledge=tuple(entry.get("knowledge", ())),
                actions=tuple(entry.get("actions", ())),
                questions=tuple(entry.get("questions", ())),
                related_topics=tuple(entry.get("related_topics", ())),
                combinations=tuple(entry.get("combinations", ())),
            )
            for entry in entries
            if isinstance(entry, dict)
            and isinstance(entry.get("id"), str)
            and isinstance(entry.get("response"), str)
        )

    def retrieve(
        self, message: str, intent: str | None = None, topic: str | None = None
    ) -> KnowledgeEntry | None:
        """Return one high-signal entry, requiring at least one reviewed match."""
        normalized_message = " ".join(message.casefold().split())
        tokens = set(re.findall(r"[a-z']+", normalized_message))
        intent_key = (intent or "").casefold()
        topic_key = (topic or "").casefold()
        scored: list[tuple[int, KnowledgeEntry]] = []
        for entry in self._entries:
            keyword_score = sum(keyword.casefold() in tokens for keyword in entry.keywords)
            phrase_score = 4 * sum(
                phrase.casefold() in normalized_message for phrase in entry.phrases
            )
            intent_score = 3 if intent_key and intent_key in {
                candidate.casefold() for candidate in entry.intents
            } else 0
            related_topic_score = 1 if topic_key and topic_key in {
                candidate.casefold() for candidate in entry.related_topics
            } else 0
            score = keyword_score + phrase_score + intent_score + related_topic_score
            if score:
                scored.append((score, entry))
        return max(scored, key=lambda item: item[0])[1] if scored else None

    @staticmethod
    def has_phrase_match(entry: KnowledgeEntry, message: str) -> bool:
        """Identify a deliberate natural-language match, not a loose keyword hit."""
        normalized_message = " ".join(message.casefold().split())
        return any(phrase.casefold() in normalized_message for phrase in entry.phrases)
