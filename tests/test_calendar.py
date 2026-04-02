import pytest
from src.calendar import generate_calendar


def test_generate_calendar_has_weeks():
    """Verify calendar output contains expected week markers."""
    output = generate_calendar(num_weeks=4)
    assert "WEEK 1" in output
    assert "WEEK 2" in output
    assert "WEEK 3" in output
    assert "WEEK 4" in output


def test_generate_calendar_has_funnel_tags():
    """Verify calendar output includes all funnel category tags."""
    output = generate_calendar(num_weeks=4)
    assert "[DISC]" in output
    assert "[MID]" in output
    assert "[$]" in output


def test_generate_calendar_has_tips():
    """Verify calendar output contains posting tips and content types."""
    output = generate_calendar(num_weeks=4)
    assert "POSTING TIPS" in output
    assert "Quick Tip" in output
    assert "Drill Demo" in output
    assert "Play Breakdown" in output
    assert "Game Film Review" in output
    assert "Motivation" in output
