"""Cross-platform export — generate platform-optimized video variants."""
import subprocess
from pathlib import Path


# Platform specs
PLATFORMS = {
    "youtube_short": {
        "width": 1080,
        "height": 1920,
        "max_seconds": 60,
        "bitrate": "8M",
        "label": "YouTube Short",
    },
    "tiktok": {
        "width": 1080,
        "height": 1920,
        "max_seconds": 60,
        "bitrate": "6M",
        "label": "TikTok",
    },
    "instagram_reels": {
        "width": 1080,
        "height": 1920,
        "max_seconds": 90,
        "bitrate": "6M",
        "label": "Instagram Reels",
    },
    "instagram_feed": {
        "width": 1080,
        "height": 1080,
        "max_seconds": 60,
        "bitrate": "5M",
        "label": "Instagram Feed (Square)",
    },
}


def export_for_platform(
    input_path: str,
    output_dir: str,
    platform: str,
    ass_path: str = "",
) -> str:
    """Export video optimized for a specific platform.

    Args:
        input_path: Source video (already captioned or raw).
        output_dir: Output directory.
        platform: Key from PLATFORMS dict.
        ass_path: Optional ASS subtitle file to burn in.

    Returns:
        Path to exported video.
    """
    spec = PLATFORMS.get(platform)
    if not spec:
        raise ValueError(f"Unknown platform: {platform}. Options: {list(PLATFORMS.keys())}")

    output_path = str(Path(output_dir) / f"{platform}.mp4")
    Path(output_dir).mkdir(parents=True, exist_ok=True)

    # Build video filter
    w, h = spec["width"], spec["height"]
    target_ratio = w / h

    # Scale and crop/pad to target dimensions
    vf_parts = []

    if target_ratio == 1.0:
        # Square (Instagram Feed) — crop center to 1:1
        vf_parts.append(f"crop=min(iw\\,ih):min(iw\\,ih):(iw-min(iw\\,ih))/2:(ih-min(iw\\,ih))/2")
        vf_parts.append(f"scale={w}:{h}")
    else:
        # Vertical 9:16 — scale to fit then crop
        vf_parts.append(f"scale={w}:{h}:force_original_aspect_ratio=increase")
        vf_parts.append(f"crop={w}:{h}")

    if ass_path and Path(ass_path).exists():
        vf_parts.append(f"ass='{ass_path}'")

    vf = ",".join(vf_parts)

    cmd = [
        "ffmpeg", "-y", "-i", input_path,
        "-vf", vf,
        "-c:v", "libx264", "-preset", "medium",
        "-b:v", spec["bitrate"], "-maxrate", spec["bitrate"],
        "-c:a", "aac", "-b:a", "128k",
        "-t", str(spec["max_seconds"]),
        "-movflags", "+faststart",
        output_path,
    ]

    subprocess.run(cmd, capture_output=True, check=True)
    return output_path


def export_all_platforms(
    input_path: str,
    output_dir: str,
    ass_path: str = "",
    platforms: list[str] | None = None,
) -> dict[str, str]:
    """Export video for all platforms.

    Returns dict of platform name -> output file path.
    """
    if platforms is None:
        platforms = ["tiktok", "instagram_reels", "instagram_feed"]

    results = {}
    for platform in platforms:
        try:
            path = export_for_platform(input_path, output_dir, platform, ass_path)
            results[platform] = path
        except Exception as e:
            results[platform] = f"ERROR: {e}"

    return results
