"""Loading and locating chatbot model artifacts without training in web requests."""

from __future__ import annotations

import pickle
import json
import shutil
from datetime import UTC, datetime
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from ChatbotWebsite.chatbot.paths import (
    ARCHIVED_MODELS_DIR,
    CANDIDATE_MODELS_DIR,
    CURRENT_MODEL_DIR,
    LEGACY_DATA_PATH,
    LEGACY_MODEL_PATH,
)


class ModelUnavailable(RuntimeError):
    """Raised when no usable chatbot model is available for inference."""


@dataclass(frozen=True)
class ModelArtifacts:
    model: Any
    words: list[str]
    classes: list[str]
    model_path: Path


class ModelManager:
    """Load the active model with legacy-artifact compatibility during migration."""

    def __init__(self) -> None:
        self._artifacts: ModelArtifacts | None = None

    def load(self) -> ModelArtifacts:
        if self._artifacts is None:
            model_path, data_path = self._active_paths()
            self._artifacts = self._load(model_path, data_path)
        return self._artifacts

    @staticmethod
    def promote_candidate(candidate_version: str) -> Path:
        """Promote only an explicitly validated candidate with passing safety tests."""
        candidate_dir = CANDIDATE_MODELS_DIR / candidate_version
        metadata_path = candidate_dir / "metadata.json"
        if not metadata_path.is_file():
            raise ModelUnavailable("The requested candidate model does not exist.")
        with metadata_path.open(encoding="utf-8") as metadata_file:
            metadata = json.load(metadata_file)
        if metadata.get("status") != "validated" or not metadata.get(
            "safety_tests_passed"
        ):
            raise ModelUnavailable(
                "Only validated candidates that pass safety tests can be promoted."
            )

        if CURRENT_MODEL_DIR.exists():
            ARCHIVED_MODELS_DIR.mkdir(parents=True, exist_ok=True)
            archive_name = datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ")
            shutil.move(str(CURRENT_MODEL_DIR), ARCHIVED_MODELS_DIR / archive_name)
        shutil.copytree(candidate_dir, CURRENT_MODEL_DIR)
        metadata["status"] = "current"
        metadata["promoted_at"] = datetime.now(UTC).isoformat()
        with (CURRENT_MODEL_DIR / "metadata.json").open("w", encoding="utf-8") as output:
            json.dump(metadata, output, indent=2)
        return CURRENT_MODEL_DIR

    @staticmethod
    def _active_paths() -> tuple[Path, Path]:
        current_model = CURRENT_MODEL_DIR / "model.keras"
        current_data = CURRENT_MODEL_DIR / "data.pickle"
        if current_model.is_file() and current_data.is_file():
            return current_model, current_data
        if LEGACY_MODEL_PATH.is_file() and LEGACY_DATA_PATH.is_file():
            return LEGACY_MODEL_PATH, LEGACY_DATA_PATH
        raise ModelUnavailable(
            "No chatbot model is available. Run the dedicated trainer to create one."
        )

    @staticmethod
    def _load(model_path: Path, data_path: Path) -> ModelArtifacts:
        try:
            with data_path.open("rb") as artifact_file:
                artifact_data = pickle.load(artifact_file)
            words, classes, *_ = artifact_data
            if not isinstance(words, list) or not isinstance(classes, list):
                raise ValueError("Model vocabulary is invalid.")

            # TensorFlow/Keras is intentionally imported only when inference is needed.
            from keras.models import load_model

            model = load_model(model_path, compile=False)
        except (OSError, ValueError, pickle.UnpicklingError, ImportError) as error:
            raise ModelUnavailable("The active chatbot model could not be loaded.") from error

        return ModelArtifacts(model=model, words=words, classes=classes, model_path=model_path)
