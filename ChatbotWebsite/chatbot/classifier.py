"""Intent classification backed by the locally managed Keras model."""

from __future__ import annotations

from dataclasses import dataclass

from ChatbotWebsite.chatbot.language import MessageNormalizer
from ChatbotWebsite.chatbot.model_manager import ModelManager


@dataclass(frozen=True)
class IntentPrediction:
    tag: str
    confidence: float


class IntentClassifier:
    def __init__(
        self,
        model_manager: ModelManager | None = None,
        normalizer: MessageNormalizer | None = None,
        threshold: float = 0.25,
    ) -> None:
        self._model_manager = model_manager or ModelManager()
        self._normalizer = normalizer or MessageNormalizer()
        self._threshold = threshold

    def predict(self, message: str) -> list[IntentPrediction]:
        artifacts = self._model_manager.load()
        message_tokens = set(self._normalizer.tokens(message))
        bag = [1 if word in message_tokens else 0 for word in artifacts.words]

        import numpy as np

        try:
            probabilities = artifacts.model.predict(np.array([bag]), verbose=0)[0]
        except TypeError:
            probabilities = artifacts.model.predict(np.array([bag]))[0]

        predictions = [
            IntentPrediction(tag=artifacts.classes[index], confidence=float(probability))
            for index, probability in enumerate(probabilities)
            if probability > self._threshold
        ]
        return sorted(predictions, key=lambda prediction: prediction.confidence, reverse=True)
