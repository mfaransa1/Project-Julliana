"""Language-agnostic token normalization used by the intent classifier."""

from __future__ import annotations

import re
from dataclasses import dataclass

from nltk.stem import WordNetLemmatizer
from nltk.tokenize import wordpunct_tokenize, word_tokenize


class MessageNormalizer:
    """Keep user wording intact while producing a conservative classifier view."""

    def __init__(self) -> None:
        self._lemmatizer = WordNetLemmatizer()

    def detect_language(self, message: str) -> "LanguageDetection":
        normalized = self.normalize_for_safety(message)
        tokens = set(re.findall(r"[a-z']+", normalized))
        scores = {
            "luo": len(tokens & LUO_MARKERS),
            "sheng": len(tokens & SHENG_MARKERS),
            "sw": len(tokens & KISWAHILI_MARKERS),
        }
        language, score = max(scores.items(), key=lambda item: item[1])
        if score == 0:
            language = "en"
        return LanguageDetection(code=language, confidence=min(1.0, score / 3))

    @staticmethod
    def normalize_for_safety(message: str) -> str:
        return re.sub(r"\s+", " ", message).strip().lower()

    def normalize_for_classifier(self, message: str) -> str:
        """Map only reviewed, unambiguous local phrases to existing intent vocabulary."""
        normalized = self.normalize_for_safety(message)
        for phrase, replacement in REVIEWED_PHRASE_MAPPINGS.items():
            normalized = normalized.replace(phrase, replacement)
        return normalized

    def tokens(self, message: str) -> list[str]:
        message = self.normalize_for_classifier(message)
        try:
            tokens = word_tokenize(message)
        except LookupError:
            # Do not download language data during a user request.
            tokens = wordpunct_tokenize(message)
        return [self._lemmatize(token.lower()) for token in tokens]

    def _lemmatize(self, token: str) -> str:
        try:
            return self._lemmatizer.lemmatize(token)
        except LookupError:
            return token


@dataclass(frozen=True)
class LanguageDetection:
    code: str
    confidence: float


# These marker sets are deliberately small. They label likely language for response
# selection and reviewed training metadata; they are not a demographic inference.
KISWAHILI_MARKERS = {
    "niko", "naskia", "nimechoka", "maisha", "nawaza", "nahitaji", "msaada",
    "sana", "leo", "sitaki", "kuishi",
}
SHENG_MARKERS = {
    "poa", "niaje", "mambo", "sasa", "fiti", "noma", "ngori", "maze", "mob",
    "rada", "buda",
}
LUO_MARKERS = {
    "amosi", "nade", "ahinya", "aonge", "chuny", "awinjo", "achandora",
    "adwaro", "ngima", "kawuono",
}

REVIEWED_PHRASE_MAPPINGS = {
    "niko down sana leo": "i am feeling very low today",
    "naskia vibaya": "i am feeling bad",
    "nimechoka maisha": "i am tired of life",
    "nimelemewa na kazi": "i am overwhelmed by work",
    "naskia pressure mingi": "i am feeling a lot of pressure",
    "niko na stress": "i am stressed",
    "nawaza sana": "i am overthinking a lot",
}
