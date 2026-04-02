"""Tests for auto-hook detection."""
from src.hooks import score_sentence, detect_hook


def test_score_sentence_hook_words():
    score = score_sentence("This is the biggest mistake coaches make")
    assert score > 0.3


def test_score_sentence_boring():
    score = score_sentence("The point guard passes the ball")
    assert score < 0.4


def test_score_sentence_question():
    score = score_sentence("Why does every team run this play?")
    assert score > 0.3


def test_score_sentence_empty():
    assert score_sentence("") == 0.0


def test_score_sentence_short():
    assert score_sentence("Hi") == 0.0


def test_detect_hook_finds_best():
    transcript = {
        "text": "Today we look at plays. This play destroys every zone defense. The point guard starts here.",
        "segments": []
    }
    result = detect_hook(transcript)
    assert "destroys" in result["sentence"].lower() or "zone" in result["sentence"].lower()
    assert result["score"] > 0.2
    assert result["hook_text"] != ""
    assert result["accent_word"] != ""


def test_detect_hook_empty_transcript():
    result = detect_hook({"text": "", "segments": []})
    assert result["sentence"] == ""
    assert result["score"] == 0.0


def test_detect_hook_max_words():
    transcript = {
        "text": "This is the number one biggest mistake that every single coach makes in basketball.",
        "segments": []
    }
    result = detect_hook(transcript, max_words=4)
    assert len(result["hook_text"].split()) <= 4
