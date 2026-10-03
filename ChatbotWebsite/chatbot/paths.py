"""Stable filesystem locations for chatbot data and model artifacts."""

from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[2]
CHATBOT_ROOT = Path(__file__).resolve().parent
DATA_DIR = CHATBOT_ROOT.parent / "static" / "data"
MINDFULNESS_DIR = CHATBOT_ROOT.parent / "static" / "mindfulness"
MODELS_DIR = PROJECT_ROOT / "models"
CURRENT_MODEL_DIR = MODELS_DIR / "current"
CANDIDATE_MODELS_DIR = MODELS_DIR / "candidates"
ARCHIVED_MODELS_DIR = MODELS_DIR / "archive"
TRAINING_DATA_DIR = PROJECT_ROOT / "training_data"
APPROVED_EXAMPLES_PATH = TRAINING_DATA_DIR / "approved_examples.json"
LANGUAGE_DATASET_PATHS = (
    TRAINING_DATA_DIR / "english.json",
    TRAINING_DATA_DIR / "kiswahili.json",
    TRAINING_DATA_DIR / "sheng.json",
    TRAINING_DATA_DIR / "luo.json",
)

INTENTS_PATH = DATA_DIR / "intents.json"
TESTS_PATH = DATA_DIR / "tests.json"
TOPICS_PATH = DATA_DIR / "topics.json"
MINDFULNESS_PATH = MINDFULNESS_DIR / "mindfulness.json"
CONVERSATION_STARTERS_PATH = DATA_DIR / "conversation_starters.json"

LEGACY_MODEL_PATH = PROJECT_ROOT / "chatbot-model.h5"
LEGACY_DATA_PATH = PROJECT_ROOT / "data.pickle"
