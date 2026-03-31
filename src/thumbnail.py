"""Thumbnail generator — cartoon filter + bold white/yellow text overlay."""
from pathlib import Path

import cv2
import numpy as np
from PIL import Image, ImageDraw, ImageFont


def apply_cartoon_filter(image: Image.Image, strength: str = "medium") -> Image.Image:
    """Apply cartoon/illustration effect using bilateral filtering + edge detection."""
    iterations = {"light": 3, "medium": 5, "heavy": 7}.get(strength, 5)
    img_array = np.array(image)
    img_bgr = cv2.cvtColor(img_array, cv2.COLOR_RGB2BGR)
    gray = cv2.cvtColor(img_bgr, cv2.COLOR_BGR2GRAY)
    gray = cv2.medianBlur(gray, 5)
    edges = cv2.adaptiveThreshold(
        gray, 255, cv2.ADAPTIVE_THRESH_MEAN_C, cv2.THRESH_BINARY, blockSize=9, C=9
    )
    color = img_bgr.copy()
    for _ in range(iterations):
        color = cv2.bilateralFilter(color, d=9, sigmaColor=75, sigmaSpace=75)
    edges_bgr = cv2.cvtColor(edges, cv2.COLOR_GRAY2BGR)
    cartoon = cv2.bitwise_and(color, edges_bgr)
    cartoon_rgb = cv2.cvtColor(cartoon, cv2.COLOR_BGR2RGB)
    return Image.fromarray(cartoon_rgb)


def _load_font(font_path: str | None, size: int) -> ImageFont.FreeTypeFont | ImageFont.ImageFont:
    """Load font, falling back to default if path is None or missing."""
    if font_path:
        try:
            return ImageFont.truetype(font_path, size)
        except (OSError, IOError):
            pass
    for path in [
        Path.home() / "Library/Fonts/Montserrat-ExtraBold.ttf",
        Path("/usr/share/fonts/truetype/montserrat/Montserrat-ExtraBold.ttf"),
    ]:
        if path.exists():
            return ImageFont.truetype(str(path), size)
    return ImageFont.load_default(size=size)


def add_text_overlay(
    image: Image.Image,
    hook_text: str,
    accent_word: str,
    font_path: str | None = None,
    primary_color: str = "#FFFFFF",
    accent_color: str = "#FFFF00",
    stroke_color: str = "#000000",
    stroke_width: int = 4,
    position: str = "right",
) -> Image.Image:
    """Add bold hook text to thumbnail with accent word in yellow."""
    result = image.copy()
    draw = ImageDraw.Draw(result)
    width, height = result.size
    font_size = max(48, height // 8)
    font = _load_font(font_path, font_size)

    words = hook_text.upper().split()
    accent_upper = accent_word.upper()

    if position == "right":
        x_base = width * 0.55
    elif position == "left":
        x_base = width * 0.05
    else:
        x_base = width * 0.5

    y_start = height * 0.25
    line_height = font_size * 1.3

    for i, word in enumerate(words):
        y = y_start + i * line_height
        color = accent_color if word == accent_upper else primary_color
        draw.text((x_base, y), word, font=font, fill=color,
                  stroke_width=stroke_width, stroke_fill=stroke_color)

    return result


def generate_thumbnail(
    source_image_path: str,
    hook_text: str,
    accent_word: str,
    config: dict,
    output_dir: str,
) -> str:
    """Generate a cartoon-style thumbnail with text overlay."""
    brand = config["brand"]
    thumb_config = config["thumbnail"]

    img = Image.open(source_image_path).convert("RGB")
    img = img.resize((thumb_config["width"], thumb_config["height"]), Image.LANCZOS)
    img = apply_cartoon_filter(img, strength=thumb_config.get("cartoon_strength", "medium"))

    font_path = None
    candidate = Path.home() / "Library/Fonts/Montserrat-ExtraBold.ttf"
    if candidate.exists():
        font_path = str(candidate)

    img = add_text_overlay(
        image=img,
        hook_text=hook_text,
        accent_word=accent_word,
        font_path=font_path,
        primary_color=brand["primary_color"],
        accent_color=brand["accent_color"],
        stroke_color=brand["stroke_color"],
        stroke_width=brand["stroke_width"],
        position=thumb_config.get("text_position", "right"),
    )

    output_path = Path(output_dir) / "thumbnail.jpg"
    output_path.parent.mkdir(parents=True, exist_ok=True)
    img.save(str(output_path), "JPEG", quality=95)
    return str(output_path)
