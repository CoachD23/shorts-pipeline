"""Tests for YouTube Analytics module."""
from src.analytics import format_analytics_report


def test_format_analytics_report_single_video():
    response = {
        "columnHeaders": [
            {"name": "views"}, {"name": "likes"}, {"name": "shares"},
        ],
        "rows": [[1500, 45, 12]],
    }
    report = format_analytics_report(response, "Test Video")
    assert "1,500" in report
    assert "45" in report
    assert "Test Video" in report


def test_format_analytics_report_multi_video():
    response = {
        "columnHeaders": [
            {"name": "video"}, {"name": "views"}, {"name": "estimatedMinutesWatched"},
            {"name": "averageViewDuration"}, {"name": "likes"},
        ],
        "rows": [
            ["vid1", 5000, 200, 45.5, 100],
            ["vid2", 3000, 120, 30.2, 50],
        ],
    }
    report = format_analytics_report(response, "Channel")
    assert "vid1" in report
    assert "5,000" in report
    assert "#1" in report
    assert "#2" in report


def test_format_analytics_report_empty():
    response = {"columnHeaders": [], "rows": []}
    report = format_analytics_report(response)
    assert "No data" in report
