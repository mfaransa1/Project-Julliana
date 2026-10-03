"""Configured prompts displayed before a new conversation begins."""

from __future__ import annotations

import json

from ChatbotWebsite.chatbot.paths import CONVERSATION_STARTERS_PATH


def get_conversation_starters() -> list[str]:
    with CONVERSATION_STARTERS_PATH.open(encoding="utf-8") as starter_file:
        starters = json.load(starter_file).get("starters", [])
    return [item for item in starters if isinstance(item, str) and item.strip()]
