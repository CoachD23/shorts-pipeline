"""YouTube description generator — SEO-optimized from transcript."""
import re
from pathlib import Path


def _slugify(title: str) -> str:
    """Convert title to URL slug."""
    slug = title.lower().strip()
    slug = re.sub(r"[^\w\s-]", "", slug)
    slug = re.sub(r"[\s_]+", "-", slug)
    return slug.strip("-")


def _format_timestamp(seconds: float) -> str:
    """Convert seconds to M:SS format."""
    m = int(seconds // 60)
    s = int(seconds % 60)
    return f"{m}:{s:02d}"


def detect_timestamps(segments: list[dict], pause_threshold: float = 1.5) -> list[dict]:
    """Detect topic boundaries from pauses between segments."""
    timestamps = []
    if not segments:
        return timestamps
    timestamps.append({
        "time": _format_timestamp(segments[0]["start"]),
        "text": segments[0]["text"].strip()[:60],
    })
    for i in range(1, len(segments)):
        gap = segments[i]["start"] - segments[i - 1]["end"]
        if gap >= pause_threshold:
            timestamps.append({
                "time": _format_timestamp(segments[i]["start"]),
                "text": segments[i]["text"].strip()[:60],
            })
    return timestamps


def generate_description(transcript: dict, title: str, config: dict) -> str:
    """Generate a full YouTube description from transcript and config."""
    yt_config = config["youtube"]
    blog_config = config["blog"]

    full_text = transcript.get("text", "")
    sentences = re.split(r"(?<=[.!?])\s+", full_text)
    summary = " ".join(sentences[:3]).strip()

    slug = _slugify(title)
    blog_url = f"{blog_config['base_url']}/{slug}"

    segments = transcript.get("segments", [])
    timestamps = detect_timestamps(segments)
    timestamp_lines = "\n".join(f"{ts['time']} - {ts['text']}" for ts in timestamps)

    tags = " ".join(f"#{tag.replace(' ', '')}" for tag in yt_config.get("default_tags", []))

    return f"""🏀 {title} — Princeton Offense Breakdown

{summary}

📋 Full Written Breakdown:
{blog_url}

⏱️ Timestamps:
{timestamp_lines}

🏷️ Tags:
{tags}

📚 More Princeton Offense Content:
► Subscribe: https://www.youtube.com/@CoachPrincetonBasketball?sub_confirmation=1

© CoachPrincetonBasketball.com"""


def save_description(transcript: dict, title: str, config: dict, output_dir: Path) -> Path:
    """Generate and save YouTube description to file."""
    output_dir.mkdir(parents=True, exist_ok=True)
    desc = generate_description(transcript, title, config)
    desc_path = output_dir / "description.txt"
    desc_path.write_text(desc)
    return desc_path
