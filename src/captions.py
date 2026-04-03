"""Kinetic caption generator — produces ASS subtitles with white-to-yellow word highlighting."""
from pathlib import Path


def _hex_to_ass_color(hex_color: str) -> str:
    """Convert hex color (#RRGGBB) to ASS color (&HBBGGRR&)."""
    hex_color = hex_color.lstrip("#")
    r, g, b = hex_color[0:2], hex_color[2:4], hex_color[4:6]
    return f"&H00{b}{g}{r}&"


def _format_time(seconds: float) -> str:
    """Convert seconds to ASS timestamp (H:MM:SS.CC)."""
    h = int(seconds // 3600)
    m = int((seconds % 3600) // 60)
    s = int(seconds % 60)
    cs = int((seconds % 1) * 100)
    return f"{h}:{m:02d}:{s:02d}.{cs:02d}"


def group_words(words: list[dict], words_per_group: int = 3) -> list[dict]:
    """Group words into chunks for display."""
    groups = []
    for i in range(0, len(words), words_per_group):
        chunk = words[i:i + words_per_group]
        groups.append({
            "words": [w["word"].strip() for w in chunk],
            "start": chunk[0]["start"],
            "end": chunk[-1]["end"],
            "word_timings": [(w["word"].strip(), w["start"], w["end"]) for w in chunk],
        })
    return groups


def generate_kinetic_ass(transcript: dict, config: dict) -> str:
    """Generate ASS subtitle content with kinetic word highlighting.

    Each word group appears as a dialogue line. Within each group's display time,
    individual words highlight from white to yellow as they are spoken.
    """
    brand = config["brand"]
    captions = config["captions"]

    primary_ass = _hex_to_ass_color(brand["primary_color"])
    accent_ass = _hex_to_ass_color(brand["accent_color"])
    stroke_ass = _hex_to_ass_color(brand["stroke_color"])
    font = brand["font"]
    font_size = captions["font_size"]
    stroke_width = brand["stroke_width"]
    wpg = captions["words_per_group"]

    header = f"""[Script Info]
Title: Kinetic Captions
ScriptType: v4.00+
PlayResX: 1080
PlayResY: 1920
WrapStyle: 0

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: Kinetic,{font},{font_size},{primary_ass},&H000000FF&,{stroke_ass},&H80000000&,-1,0,0,0,100,100,0,0,1,{stroke_width},2,5,40,40,400,1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text"""

    lines = [header]

    all_words = []
    for segment in transcript.get("segments", []):
        all_words.extend(segment.get("words", []))

    if not all_words:
        import logging
        logging.warning("No word-level timestamps in transcript — captions will be empty. "
                        "Ensure transcribe_video is called with word_timestamps=True.")

    groups = group_words(all_words, wpg)

    for group in groups:
        for word_text, word_start, word_end in group["word_timings"]:
            w_start = _format_time(word_start)
            w_end = _format_time(word_end)

            parts = []
            for w, ws, we in group["word_timings"]:
                if w == word_text and ws == word_start:
                    parts.append(f"{{\\c{accent_ass}}}{w}")
                else:
                    parts.append(f"{{\\c{primary_ass}}}{w}")

            text = " ".join(parts)
            lines.append(f"Dialogue: 0,{w_start},{w_end},Kinetic,,0,0,0,,{text}")

    return "\n".join(lines)


def save_captions(transcript: dict, config: dict, output_dir: Path) -> Path:
    """Generate and save ASS caption file."""
    output_dir.mkdir(parents=True, exist_ok=True)
    ass_content = generate_kinetic_ass(transcript, config)
    ass_path = output_dir / "captions.ass"
    ass_path.write_text(ass_content)
    return ass_path
