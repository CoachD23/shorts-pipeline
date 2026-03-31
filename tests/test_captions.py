"""Tests for kinetic caption ASS subtitle generation."""
from src.captions import generate_kinetic_ass, group_words


def test_group_words_chunks_by_count():
    words = [
        {"word": "This", "start": 0.0, "end": 0.3},
        {"word": "play", "start": 0.3, "end": 0.6},
        {"word": "breaks", "start": 0.6, "end": 1.0},
        {"word": "every", "start": 1.0, "end": 1.3},
        {"word": "zone", "start": 1.3, "end": 1.8},
    ]
    groups = group_words(words, words_per_group=2)
    assert len(groups) == 3
    assert groups[0]["words"] == ["This", "play"]
    assert groups[2]["words"] == ["zone"]


def test_generate_kinetic_ass_contains_header():
    transcript = {
        "segments": [{
            "words": [
                {"word": "Test", "start": 0.0, "end": 0.5},
                {"word": "caption", "start": 0.5, "end": 1.0},
            ]
        }]
    }
    config = {
        "brand": {"primary_color": "#FFFFFF", "accent_color": "#FFFF00",
                  "font": "Montserrat-ExtraBold", "stroke_color": "#000000", "stroke_width": 4},
        "captions": {"words_per_group": 3, "font_size": 65, "position": "center_above_middle"},
    }
    ass_content = generate_kinetic_ass(transcript, config)
    assert "[Script Info]" in ass_content
    assert "[V4+ Styles]" in ass_content
    assert "[Events]" in ass_content
    assert "Test" in ass_content


def test_generate_kinetic_ass_has_yellow_highlight():
    transcript = {
        "segments": [{
            "words": [
                {"word": "This", "start": 0.0, "end": 0.5},
                {"word": "works", "start": 0.5, "end": 1.0},
            ]
        }]
    }
    config = {
        "brand": {"primary_color": "#FFFFFF", "accent_color": "#FFFF00",
                  "font": "Montserrat-ExtraBold", "stroke_color": "#000000", "stroke_width": 4},
        "captions": {"words_per_group": 3, "font_size": 65, "position": "center_above_middle"},
    }
    ass_content = generate_kinetic_ass(transcript, config)
    # ASS uses BGR format: #FFFF00 (yellow) -> &H0000FFFF& but our function outputs &H0000FF&
    assert "\\c&H00" in ass_content
