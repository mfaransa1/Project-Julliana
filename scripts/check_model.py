"""Fail fast when a deployment has no usable local chatbot model artifacts."""

from __future__ import annotations

import sys
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
CURRENT_MODEL_FILES = (
    PROJECT_ROOT / "models" / "current" / "model.keras",
    PROJECT_ROOT / "models" / "current" / "data.pickle",
)
LEGACY_MODEL_FILES = (
    PROJECT_ROOT / "chatbot-model.h5",
    PROJECT_ROOT / "data.pickle",
)


def has_complete_pair(files: tuple[Path, Path]) -> bool:
    return all(path.is_file() and path.stat().st_size > 0 for path in files)


def main() -> int:
    if has_complete_pair(CURRENT_MODEL_FILES):
        print("Chatbot model preflight passed: validated current artifacts found.")
        return 0
    if has_complete_pair(LEGACY_MODEL_FILES):
        print("Chatbot model preflight passed: legacy artifacts found.")
        return 0

    print(
        "Chatbot model preflight failed: deploy a complete models/current pair or "
        "the legacy chatbot-model.h5 and data.pickle artifacts.",
        file=sys.stderr,
    )
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
