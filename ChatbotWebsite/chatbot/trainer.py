"""Explicit candidate-model training; never invoked from a Flask request."""

from __future__ import annotations

import json
import pickle
from datetime import UTC, datetime
from pathlib import Path

import numpy as np

from ChatbotWebsite.chatbot.language import MessageNormalizer
from ChatbotWebsite.chatbot.paths import (
    APPROVED_EXAMPLES_PATH,
    CANDIDATE_MODELS_DIR,
    INTENTS_PATH,
    LANGUAGE_DATASET_PATHS,
)


def _load_examples(
    intents_path: Path, approved_examples_path: Path
) -> tuple[list[tuple[str, str]], str]:
    with intents_path.open(encoding="utf-8") as intent_file:
        intents = json.load(intent_file)["intents"]
    examples = [
        (pattern, intent["tag"])
        for intent in intents
        for pattern in intent["patterns"]
    ]

    with approved_examples_path.open(encoding="utf-8") as approved_file:
        approved_data = json.load(approved_file)
    valid_tags = {intent["tag"] for intent in intents}
    for example in approved_data.get("examples", []):
        pattern = example.get("pattern", "").strip()
        tag = example.get("tag")
        if pattern and tag in valid_tags:
            examples.append((pattern, tag))
    for dataset_path in LANGUAGE_DATASET_PATHS:
        with dataset_path.open(encoding="utf-8") as dataset_file:
            dataset = json.load(dataset_file)
        for example in dataset.get("examples", []):
            pattern = example.get("pattern", "").strip()
            tag = example.get("tag")
            if pattern and tag in valid_tags:
                examples.append((pattern, tag))
    return examples, str(approved_data.get("dataset_version", "1"))


def train(
    intents_path: Path = INTENTS_PATH,
    approved_examples_path: Path = APPROVED_EXAMPLES_PATH,
    output_dir: Path | None = None,
) -> Path:
    """Create a candidate model from baseline plus reviewed training examples."""
    from keras.layers import Dense, Dropout, Input
    from keras.models import Sequential
    from keras.optimizers import Adam

    examples, dataset_version = _load_examples(intents_path, approved_examples_path)
    normalizer = MessageNormalizer()
    documents = [(normalizer.tokens(pattern), tag) for pattern, tag in examples]
    words = sorted({word for tokens, _ in documents for word in tokens})
    classes = sorted({tag for _, tag in documents})
    training_rows = []
    output_rows = []
    for tokens, tag in documents:
        token_set = set(tokens)
        training_rows.append([1 if word in token_set else 0 for word in words])
        output_rows.append([1 if item == tag else 0 for item in classes])

    model = Sequential(
        [
            Input(shape=(len(words),)),
            Dense(256, activation="relu"),
            Dropout(0.4),
            Dense(128, activation="relu"),
            Dropout(0.4),
            Dense(64, activation="relu"),
            Dropout(0.4),
            Dense(len(classes), activation="softmax"),
        ]
    )
    model.compile(
        loss="categorical_crossentropy",
        optimizer=Adam(learning_rate=0.001),
        metrics=["accuracy"],
    )
    history = model.fit(
        np.array(training_rows), np.array(output_rows), epochs=300, batch_size=10
    )

    version = datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ")
    candidate_dir = output_dir or CANDIDATE_MODELS_DIR / version
    candidate_dir.mkdir(parents=True, exist_ok=False)
    model.save(candidate_dir / "model.keras")
    with (candidate_dir / "data.pickle").open("wb") as artifact_file:
        pickle.dump((words, classes, training_rows, output_rows), artifact_file)
    metadata = {
        "version": version,
        "created_at": datetime.now(UTC).isoformat(),
        "dataset_version": dataset_version,
        "validation_accuracy": None,
        "training_accuracy": float(history.history["accuracy"][-1]),
        "safety_tests_passed": False,
        "status": "candidate",
    }
    with (candidate_dir / "metadata.json").open("w", encoding="utf-8") as metadata_file:
        json.dump(metadata, metadata_file, indent=2)
    return candidate_dir


if __name__ == "__main__":
    print(train())
