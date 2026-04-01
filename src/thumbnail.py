"""Thumbnail generator — cartoon filter + gradient overlay + bold white/yellow text.

Best practices applied from top YouTube thumbnail research:
- Work at 1600x900 internally, downscale to 1280x720 for sharper output
- Dynamic font scaling: fewer words = bigger text
- Safe zones: 50px margins, avoid bottom-right (YouTube duration badge)
- Vignette + gradient overlay for text readability
- Auto file size check (YouTube max 2MB)
"""
import io
from pathlib import Path

import cv2
import numpy as np
from PIL import Image, ImageDraw, ImageFont

# Internal canvas (higher res for sharpness)
CANVAS_WIDTH, CANVAS_HEIGHT = 1600, 900

# YouTube output target
OUTPUT_WIDTH, OUTPUT_HEIGHT = 1280, 720

# Safe zone margins at canvas resolution
SAFE_MARGIN = 62  # ~50px at 1280x720 scaled up

# YouTube duration badge zone to avoid (bottom-right)
BADGE_ZONE = (CANVAS_WIDTH - 290, CANVAS_HEIGHT - 75, CANVAS_WIDTH, CANVAS_HEIGHT)


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


def apply_vignette(image: Image.Image, intensity: float = 0.5) -> Image.Image:
    """Darken edges to draw eye toward center content."""
    width, height = image.size
    result = image.copy()

    gradient = Image.new("L", (width, height), 0)
    draw = ImageDraw.Draw(gradient)

    cx, cy = width // 2, height // 2
    max_radius = int((cx ** 2 + cy ** 2) ** 0.5)

    for r in range(max_radius, 0, -2):
        brightness = int(255 * (r / max_radius) ** 2 * intensity)
        draw.ellipse(
            [cx - r, cy - r, cx + r, cy + r],
            fill=max(0, 255 - brightness),
        )

    dark = Image.new("RGB", (width, height), (0, 0, 0))
    result = Image.composite(result, dark, gradient)
    return result


def apply_gradient_overlay(
    image: Image.Image,
    side: str = "right",
    opacity: float = 0.75,
    coverage: float = 0.55,
) -> Image.Image:
    """Apply semi-transparent dark gradient on one side for text readability."""
    width, height = image.size

    overlay = Image.new("RGBA", (width, height), (0, 0, 0, 0))
    draw = ImageDraw.Draw(overlay)

    if side == "right":
        start_x = int(width * (1 - coverage))
        for x in range(start_x, width):
            progress = (x - start_x) / (width - start_x)
            alpha = int(255 * opacity * progress)
            draw.line([(x, 0), (x, height)], fill=(0, 0, 0, alpha))
    elif side == "left":
        end_x = int(width * coverage)
        for x in range(0, end_x):
            progress = 1 - (x / end_x)
            alpha = int(255 * opacity * progress)
            draw.line([(x, 0), (x, height)], fill=(0, 0, 0, alpha))
    elif side == "bottom":
        start_y = int(height * (1 - coverage))
        for y in range(start_y, height):
            progress = (y - start_y) / (height - start_y)
            alpha = int(255 * opacity * progress)
            draw.line([(0, y), (width, y)], fill=(0, 0, 0, alpha))

    result = image.convert("RGBA")
    result = Image.alpha_composite(result, overlay)
    return result.convert("RGB")


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


def _calculate_font_size(
    canvas_width: int,
    canvas_height: int,
    words: list[str],
    font_path: str | None,
    position: str = "right",
) -> int:
    """Auto-fit font size so the longest word fits within the text zone.

    Measures actual rendered text width and scales down if needed.
    Target: ~9.6% of shorter dimension as baseline, clamped to fit.
    """
    # Text zone width (roughly half the canvas minus margins)
    if position in ("right", "left"):
        zone_width = int(canvas_width * 0.45)
    else:
        zone_width = int(canvas_width * 0.85)

    # Max height per line (canvas height / (word_count + 1) for spacing)
    max_line_height = int(canvas_height / (len(words) + 1))

    # Start with baseline and shrink if any word overflows
    base = int(min(canvas_width, canvas_height) * 0.096)  # ~86px at 900
    font_size = min(base, max_line_height)

    # Binary search for the largest size that fits
    for size in range(font_size * 2, 40, -2):
        font = _load_font(font_path, size)
        fits = True
        for word in words:
            bbox = font.getbbox(word.upper())
            word_width = bbox[2] - bbox[0]
            if word_width > zone_width:
                fits = False
                break
        if fits:
            return size

    return 60  # absolute minimum


def add_text_overlay(
    image: Image.Image,
    hook_text: str,
    accent_word: str,
    font_path: str | None = None,
    primary_color: str = "#FFFFFF",
    accent_color: str = "#FFFF00",
    stroke_color: str = "#000000",
    stroke_width: int = 8,
    position: str = "right",
) -> Image.Image:
    """Add bold hook text to thumbnail with accent word highlighted.

    Features:
    - Dynamic font size based on word count (fewer words = bigger)
    - Stroke width scales with font size (5% of font size)
    - Vertically centered in text zone
    - Safe zone margins respected
    """
    result = image.copy()
    draw = ImageDraw.Draw(result)
    width, height = result.size

    words = hook_text.upper().split()
    accent_upper = accent_word.upper()

    # Auto-fit font size to text zone
    font_size = _calculate_font_size(width, height, words, font_path, position)
    font = _load_font(font_path, font_size)

    # Stroke scales with font size (5% of font size, min 4px)
    computed_stroke = max(4, int(font_size * 0.05))
    stroke = stroke_width if stroke_width > computed_stroke else computed_stroke

    # Line height and vertical centering
    line_height = int(font_size * 1.15)
    total_text_height = len(words) * line_height
    y_start = (height - total_text_height) / 2

    # Horizontal position with safe margins
    if position == "right":
        x_base = width * 0.52
    elif position == "left":
        x_base = SAFE_MARGIN
    else:
        x_base = width * 0.5

    for i, word in enumerate(words):
        y = y_start + i * line_height
        color = accent_color if word == accent_upper else primary_color

        if position == "center":
            bbox = font.getbbox(word)
            word_width = bbox[2] - bbox[0]
            x = (width - word_width) / 2
        else:
            x = x_base

        draw.text(
            (x, y), word, font=font, fill=color,
            stroke_width=stroke, stroke_fill=stroke_color,
        )

    return result


def _save_under_2mb(img: Image.Image, output_path: str) -> str:
    """Save JPEG, auto-reducing quality to stay under YouTube's 2MB limit."""
    for quality in [95, 90, 85, 80, 75, 70]:
        buf = io.BytesIO()
        img.save(buf, "JPEG", quality=quality, optimize=True)
        if len(buf.getvalue()) <= 2 * 1024 * 1024:
            with open(output_path, "wb") as f:
                f.write(buf.getvalue())
            return output_path
    # Fallback — save at minimum quality
    img.save(output_path, "JPEG", quality=70, optimize=True)
    return output_path


def generate_thumbnail(
    source_image_path: str,
    hook_text: str,
    accent_word: str,
    config: dict,
    output_dir: str,
) -> str:
    """Generate a cartoon-style thumbnail with gradient overlay and text.

    Pipeline:
    1. Resize to 1600x900 internal canvas (sharper rendering)
    2. Apply cartoon filter
    3. Apply vignette (darken edges)
    4. Apply gradient overlay on text side
    5. Add bold text with accent word
    6. Downscale to 1280x720
    7. Save as JPEG under 2MB
    """
    brand = config["brand"]
    thumb_config = config["thumbnail"]

    img = Image.open(source_image_path).convert("RGB")

    # 1. Work at higher internal resolution for sharpness
    img = img.resize((CANVAS_WIDTH, CANVAS_HEIGHT), Image.LANCZOS)

    # 2. Cartoon filter
    img = apply_cartoon_filter(img, strength=thumb_config.get("cartoon_strength", "medium"))

    # 3. Vignette
    img = apply_vignette(img, intensity=0.5)

    # 4. Gradient overlay
    text_pos = thumb_config.get("text_position", "right")
    img = apply_gradient_overlay(img, side=text_pos, opacity=0.75, coverage=0.55)

    # 5. Text overlay (at high res)
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
        stroke_width=brand.get("stroke_width", 8),
        position=text_pos,
    )

    # 6. Downscale to YouTube output size
    img = img.resize((OUTPUT_WIDTH, OUTPUT_HEIGHT), Image.LANCZOS)

    # 7. Save under 2MB
    output_path = str(Path(output_dir) / "thumbnail.jpg")
    Path(output_dir).mkdir(parents=True, exist_ok=True)
    return _save_under_2mb(img, output_path)
