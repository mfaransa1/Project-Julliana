"""Backward-compatible chatbot entry points.

New code should import the focused modules in this package directly.
"""

from ChatbotWebsite.chatbot.emotion import detect_emotion
from ChatbotWebsite.chatbot.engine import get_response
from ChatbotWebsite.chatbot.safety import is_crisis

__all__ = ["detect_emotion", "get_response", "is_crisis"]
