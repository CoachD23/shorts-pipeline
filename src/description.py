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


def generate_instagram_caption(transcript: dict, title: str, config: dict) -> str:
    """Generate an Instagram Reels caption from transcript.

    Instagram style: shorter, emoji-heavy, hashtag-rich, with a hook line.
    """
    full_text = transcript.get("text", "")
    sentences = re.split(r"(?<=[.!?])\s+", full_text)
    hook = sentences[0] if sentences else title
    summary = " ".join(sentences[:2]).strip()

    tags = config.get("youtube", {}).get("default_tags", [])
    hashtags = " ".join(f"#{tag.replace(' ', '')}" for tag in tags)
    # Add Instagram-specific hashtags
    hashtags += " #BasketballTips #CoachLife #HoopsEducation #BasketballIQ"

    return f"""🏀 {hook}

{summary}

💡 Full breakdown on the blog — link in bio!

{hashtags}"""


def save_instagram_caption(transcript: dict, title: str, config: dict, output_dir: Path) -> Path:
    """Save Instagram caption to file."""
    output_dir.mkdir(parents=True, exist_ok=True)
    caption = generate_instagram_caption(transcript, title, config)
    caption_path = output_dir / "instagram_caption.txt"
    caption_path.write_text(caption)
    return caption_path


def generate_blog_embed(transcript: dict, title: str, config: dict, video_id: str = "") -> str:
    """Generate ready-to-paste HTML for embedding video + transcript in blog.

    Args:
        transcript: Whisper transcript.
        title: Video title.
        config: Config dict.
        video_id: YouTube video ID (if uploaded). Empty = use placeholder.
    """
    blog_config = config.get("blog", {})
    slug = _slugify(title)

    if video_id:
        embed_html = f'<iframe width="560" height="315" src="https://www.youtube.com/embed/{video_id}" frameborder="0" allowfullscreen></iframe>'
    else:
        embed_html = f'<!-- Replace VIDEO_ID with your YouTube video ID -->\n<iframe width="560" height="315" src="https://www.youtube.com/embed/VIDEO_ID" frameborder="0" allowfullscreen></iframe>'

    # Build transcript as readable paragraphs
    full_text = transcript.get("text", "").strip()

    return f"""<!-- Blog Embed: {title} -->
<div class="video-embed">
  <h3>{title}</h3>
  {embed_html}
</div>

<div class="video-transcript">
  <details>
    <summary>📝 Read the full transcript</summary>
    <p>{full_text}</p>
  </details>
</div>
"""


def save_blog_embed(transcript: dict, title: str, config: dict, output_dir: Path, video_id: str = "") -> Path:
    """Save blog embed HTML to file."""
    output_dir.mkdir(parents=True, exist_ok=True)
    html = generate_blog_embed(transcript, title, config, video_id)
    html_path = output_dir / "blog_embed.html"
    html_path.write_text(html)
    return html_path


def generate_pinned_comment(transcript: dict, title: str) -> str:
    """Generate a pinned comment for YouTube engagement.

    Top creators always pin the first comment with a question or CTA.
    This drives engagement which the algorithm rewards.
    """
    full_text = transcript.get("text", "").strip()
    sentences = re.split(r"(?<=[.!?])\s+", full_text)

    # Generate 3 options — creator picks the best one
    options = []

    # Option 1: Question based on content
    if sentences and len(sentences[0]) > 10:
        topic = sentences[0].rstrip(".!?")
        options.append(f"What's your experience with this? Drop a comment below!")
    else:
        options.append(f"What do you think about this approach? Let me know below!")

    # Option 2: CTA to save/share
    options.append(f"Save this for your next practice! Tag a coach who needs to see this.")

    # Option 3: Challenge/engagement hook
    options.append(f"Can you run this in your next game? Comment your results!")

    return "\n\n".join([
        "PINNED COMMENT OPTIONS (pick one):",
        f"1. {options[0]}",
        f"2. {options[1]}",
        f"3. {options[2]}",
    ])


def save_pinned_comment(transcript: dict, title: str, output_dir: Path) -> Path:
    """Save pinned comment options to file."""
    output_dir.mkdir(parents=True, exist_ok=True)
    comment = generate_pinned_comment(transcript, title)
    path = output_dir / "pinned_comment.txt"
    path.write_text(comment)
    return path
