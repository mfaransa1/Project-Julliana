import importlib.util
import sys
from pathlib import Path


SAFETY_PATH = Path(__file__).resolve().parents[1] / "ChatbotWebsite" / "chatbot" / "safety.py"
spec = importlib.util.spec_from_file_location("juliana_safety", SAFETY_PATH)
assert spec and spec.loader
safety = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = safety
spec.loader.exec_module(safety)


def test_crisis_detector_prioritizes_self_harm_language():
    result = safety.CrisisDetector().check("i want to die and cannot manage this")

    assert result.is_crisis is True
    assert result.matched_pattern == "i want to die"


def test_crisis_detector_does_not_flag_a_general_support_request():
    result = safety.CrisisDetector().check("I am stressed and would like someone to talk to")

    assert result.is_crisis is False


def test_crisis_detector_recognizes_reviewed_kiswahili_and_luo_phrases():
    detector = safety.CrisisDetector()

    assert detector.check("Nataka kufa").is_crisis is True
    assert detector.check("Aonge gi dwaro mar ngima").is_crisis is True


def test_crisis_detector_recognizes_indirect_high_concern_without_flagging_an_idiom():
    detector = safety.CrisisDetector()

    assert detector.check("Everyone would be better without me").is_crisis is True
    assert detector.check("This exam is killing me").is_crisis is False
