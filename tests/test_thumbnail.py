"""Tests for thumbnail generation."""
from pathlib import Path
from PIL import Image
from src.thumbnail import apply_cartoon_filter, add_text_overlay, generate_thumbnail


def test_apply_cartoon_filter_returns_image():
    img = Image.new("RGB", (1280, 720), color=(100, 50, 50))
    result = apply_cartoon_filter(img)
    assert isinstance(result, Image.Image)
    assert result.size == (1280, 720)


def test_add_text_overlay_adds_text():
    img = Image.new("RGB", (1280, 720), color=(0, 0, 0))
    original_data = list(img.getdata())
    result = add_text_overlay(
        img, hook_text="BREAKS EVERY ZONE", accent_word="ZONE",
        font_path=None, primary_color="#FFFFFF", accent_color="#FFFF00",
    )
    result_data = list(result.getdata())
    assert original_data != result_data


def test_generate_thumbnail_creates_file(tmp_path):
    img = Image.new("RGB", (1280, 720), color=(50, 100, 50))
    source_path = tmp_path / "frame.png"
    img.save(source_path)
    config = {
        "brand": {"primary_color": "#FFFFFF", "accent_color": "#FFFF00",
                  "font": "Montserrat-ExtraBold", "stroke_color": "#000000", "stroke_width": 4},
        "thumbnail": {"width": 1280, "height": 720, "cartoon_strength": "medium", "text_position": "right"},
    }
    out_path = generate_thumbnail(
        source_image_path=str(source_path), hook_text="BREAKS EVERY ZONE",
        accent_word="ZONE", config=config, output_dir=str(tmp_path),
    )
    assert Path(out_path).exists()
    assert Path(out_path).suffix == ".jpg"
    thumb = Image.open(out_path)
    assert thumb.size == (1280, 720)
