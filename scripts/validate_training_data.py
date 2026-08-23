"""Check curated training examples before starting an expensive model run."""

from __future__ import annotations

import json
import sys
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
INTENTS_PATH = PROJECT_ROOT / "ChatbotWebsite" / "static" / "data" / "intents.json"
DATASET_PATHS = (
    PROJECT_ROOT / "training_data" / "approved_examples.json",
    PROJECT_ROOT / "training_data" / "english.json",
    PROJECT_ROOT / "training_data" / "kiswahili.json",
    PROJECT_ROOT / "training_data" / "sheng.json",
    PROJECT_ROOT / "training_data" / "luo.json",
)


def main() -> int:
    with INTENTS_PATH.open(encoding="utf-8") as intent_file:
        tags = {intent["tag"] for intent in json.load(intent_file)["intents"]}
    seen: set[tuple[str, str]] = set()
    errors: list[str] = []
    count = 0
    for path in DATASET_PATHS:
        with path.open(encoding="utf-8") as data_file:
            examples = json.load(data_file).get("examples", [])
        for example in examples:
            tag = example.get("tag")
            pattern = " ".join(example.get("pattern", "").split())
            count += 1
            if tag not in tags:
                errors.append(f"{path.name}: unknown intent tag {tag!r}")
            if not pattern:
                errors.append(f"{path.name}: empty training pattern")
            if (tag, pattern.casefold()) in seen:
                errors.append(f"{path.name}: duplicate pattern for {tag!r}: {pattern!r}")
            seen.add((tag, pattern.casefold()))
    if errors:
        print("Training-data validation failed:\n- " + "\n- ".join(errors), file=sys.stderr)
        return 1
    print(f"Training-data validation passed: {count} curated examples across {len(DATASET_PATHS)} files.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
