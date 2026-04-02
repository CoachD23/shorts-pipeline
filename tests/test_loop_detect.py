"""Tests for seamless loop detection."""
from PIL import Image
from src.loop_detect import calculate_frame_similarity


def test_identical_frames_high_similarity(tmp_path):
    img = Image.new("RGB", (320, 180), color=(100, 50, 50))
    p1 = tmp_path / "f1.png"
    p2 = tmp_path / "f2.png"
    img.save(p1)
    img.save(p2)
    score = calculate_frame_similarity(str(p1), str(p2))
    assert score >= 0.99


def test_different_frames_low_similarity(tmp_path):
    img1 = Image.new("RGB", (320, 180), color=(0, 0, 0))
    img2 = Image.new("RGB", (320, 180), color=(255, 255, 255))
    p1 = tmp_path / "f1.png"
    p2 = tmp_path / "f2.png"
    img1.save(p1)
    img2.save(p2)
    score = calculate_frame_similarity(str(p1), str(p2))
    assert score < 0.5


def test_similar_frames_moderate(tmp_path):
    img1 = Image.new("RGB", (320, 180), color=(100, 100, 100))
    img2 = Image.new("RGB", (320, 180), color=(120, 100, 100))
    p1 = tmp_path / "f1.png"
    p2 = tmp_path / "f2.png"
    img1.save(p1)
    img2.save(p2)
    score = calculate_frame_similarity(str(p1), str(p2))
    assert 0.9 <= score <= 1.0
