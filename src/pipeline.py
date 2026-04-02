#!/usr/bin/env python3
"""Shorts Pipeline — convert raw video to captioned YouTube Shorts."""
import argparse
import sys
from datetime import date
from pathlib import Path

import yaml

from src.transcribe import transcribe_video, save_transcript
from src.captions import save_captions
from src.thumbnail import generate_thumbnail
from src.description import generate_description, save_description, save_instagram_caption, save_blog_embed
from src.video import process_video, extract_frame
from src.upload import upload_video
from src.music import find_music_file, build_music_ffmpeg_args
from src.hooks import detect_hook


def load_config(config_path: str) -> dict:
    """Load YAML config file."""
    with open(config_path) as f:
        return yaml.safe_load(f)


def run_pipeline(
    input_path: str,
    title: str,
    hook_text: str = "",
    accent_word: str = "",
    crop_strategy: str = "center",
    upload: bool = False,
    config_path: str = "config.yaml",
    output_base: str = "output",
    source_image: str = "",       # NEW
    no_filter: bool = False,      # NEW
    music_dir: str = "music",
    variants: int = 0,
    publish_at: str = "",
) -> dict:
    """Run the full pipeline on a single video."""
    config = load_config(config_path)

    slug = title.lower().replace(" ", "-")[:40]
    output_dir = Path(output_base) / f"{date.today().isoformat()}-{slug}"
    output_dir.mkdir(parents=True, exist_ok=True)

    print(f"[1/6] Transcribing with Whisper...")
    transcript = transcribe_video(input_path, model_size="medium")

    print(f"[2/6] Saving transcript...")
    json_path, md_path = save_transcript(transcript, output_dir, title)

    # Auto-detect hook for thumbnail
    hook_suggestion = detect_hook(transcript)
    if hook_suggestion["score"] > 0.2 and not hook_text:
        print(f"  Suggested hook: \"{hook_suggestion['hook_text']}\" (accent: {hook_suggestion['accent_word']})")
        hook_text = hook_suggestion["hook_text"]
        accent_word = hook_suggestion["accent_word"]

    # Find background music (optional)
    music_path = find_music_file(music_dir)
    if music_path:
        print(f"[2.5/6] Found background music: {Path(music_path).name}")

    print(f"[3/6] Generating kinetic captions...")
    ass_path = save_captions(transcript, config, output_dir)

    print(f"[4/6] Generating thumbnail...")
    if source_image:
        frame_path = source_image
    else:
        frame_path = extract_frame(input_path, str(output_dir / "frame.png"), timestamp=1.0)

    # Override cartoon filter if --no-filter
    thumb_config = dict(config)
    if no_filter:
        thumb_config = {**config, "thumbnail": {**config.get("thumbnail", {}), "cartoon_strength": "none"}}

    thumb_path = generate_thumbnail(
        source_image_path=frame_path,
        hook_text=hook_text or title.upper(),
        accent_word=accent_word or title.split()[-1].upper(),
        config=thumb_config if no_filter else config,
        output_dir=str(output_dir),
    )

    variant_paths = []
    if variants > 0:
        from src.thumbnail import generate_thumbnail_variants
        variant_paths = generate_thumbnail_variants(
            source_image_path=frame_path,
            hook_text=hook_text or title.upper(),
            accent_word=accent_word or title.split()[-1].upper(),
            config=thumb_config if no_filter else config,
            output_dir=str(output_dir),
            variant_count=variants,
        )

    print(f"[5/6] Generating YouTube description...")
    desc_path = save_description(transcript, title, config, output_dir)

    # Instagram caption
    ig_path = save_instagram_caption(transcript, title, config, output_dir)

    print(f"[6/6] Processing video with FFmpeg...")
    video_outputs = process_video(
        input_path=input_path,
        ass_path=str(ass_path),
        output_dir=str(output_dir),
        crop_strategy=crop_strategy,
    )

    result = {
        "output_dir": str(output_dir),
        "transcript_json": str(json_path),
        "transcript_md": str(md_path),
        "captions_ass": str(ass_path),
        "thumbnail": thumb_path,
        "description": str(desc_path),
        "instagram_caption": str(ig_path),
        "videos": video_outputs,
        "music": music_path or "",
        "hook_suggestion": hook_suggestion,
    }
    if variant_paths:
        result["thumbnail_variants"] = variant_paths

    if upload:
        print("Uploading to YouTube...")
        desc_text = desc_path.read_text()
        tags = config["youtube"].get("default_tags", [])
        privacy = config["youtube"].get("default_privacy", "private")
        short_path = video_outputs.get("short-captioned.mp4", "")
        if short_path:
            video_id = upload_video(
                video_path=short_path,
                title=title,
                description=desc_text,
                tags=tags,
                privacy=privacy,
                thumbnail_path=thumb_path,
                publish_at=publish_at or None,
            )
            result["youtube_id"] = video_id
            result["youtube_url"] = f"https://youtube.com/shorts/{video_id}"
            print(f"Uploaded: https://youtube.com/shorts/{video_id}")

    # Blog embed HTML
    blog_embed_path = save_blog_embed(
        transcript, title, config, output_dir,
        video_id=result.get("youtube_id", ""),
    )
    result["blog_embed"] = str(blog_embed_path)

    print(f"\nDone! Output: {output_dir}")
    return result


def main():
    parser = argparse.ArgumentParser(description="Process video into YouTube Short")
    parser.add_argument("input", nargs="?", help="Path to input video file")
    parser.add_argument("--title", required=True, help="Video title")
    parser.add_argument("--hook", default="", help="Thumbnail hook text (2-4 words)")
    parser.add_argument("--accent", default="", help="Word to highlight yellow in thumbnail")
    parser.add_argument("--crop", choices=["center", "blur", "none"], default="center",
                        help="Vertical crop strategy for horizontal videos")
    parser.add_argument("--no-upload", action="store_true", help="Skip YouTube upload")
    parser.add_argument("--batch", action="store_true", help="Process all files in inbox/")
    parser.add_argument("--config", default="config.yaml", help="Path to config file")
    parser.add_argument("--output", default="output", help="Output base directory")
    parser.add_argument("--source-image", default="", help="Path to custom thumbnail image (skip frame extraction)")
    parser.add_argument("--no-filter", action="store_true", help="Skip cartoon filter on thumbnail (use raw photo)")
    parser.add_argument("--no-music", action="store_true", help="Skip background music")
    parser.add_argument("--music-dir", default="music", help="Directory containing music files")
    parser.add_argument("--publish-at", default="", help="Schedule publish time (ISO 8601, e.g. '2026-04-02T09:00:00Z')")
    parser.add_argument("--variants", type=int, default=0, help="Generate N thumbnail variants for A/B testing (0=off)")
    parser.add_argument("--analytics", action="store_true", help="Show channel analytics instead of processing video")
    parser.add_argument("--analytics-video", default="", help="Show analytics for a specific video ID")
    parser.add_argument("--analytics-days", type=int, default=28, help="Analytics lookback period in days")
    parser.add_argument("--extract-clips", type=int, default=0, help="Extract N best clips from long video (0=off)")
    args = parser.parse_args()

    if args.analytics or args.analytics_video:
        from src.analytics import get_analytics
        import yaml
        config = yaml.safe_load(open(args.config))
        channel_id = config.get("youtube", {}).get("channel_id", "")
        report = get_analytics(channel_id, args.analytics_video, args.analytics_days)
        print(report)
        return 0

    if args.extract_clips > 0 and args.input:
        from src.transcribe import transcribe_video
        from src.clips import extract_clips_from_video
        import yaml
        config = yaml.safe_load(open(args.config))
        print(f"Transcribing {args.input}...")
        transcript = transcribe_video(args.input)
        print(f"Finding top {args.extract_clips} clips...")
        clips = extract_clips_from_video(args.input, transcript, args.output, args.extract_clips)
        for i, clip in enumerate(clips, 1):
            print(f"  Clip {i}: {clip['start']:.1f}s - {clip['end']:.1f}s (score: {clip['score']:.2f})")
            print(f"    \"{clip['text']}\"")
            print(f"    → {clip['path']}")
        print(f"\n{len(clips)} clips extracted to {args.output}/")
        return 0

    if args.batch:
        inbox = Path("inbox")
        video_exts = {".mp4", ".mov", ".avi", ".mkv", ".webm"}
        videos = [f for f in inbox.iterdir() if f.suffix.lower() in video_exts]
        if not videos:
            print("No videos found in inbox/")
            return 1
        for video in sorted(videos):
            print(f"\n{'='*60}")
            print(f"Processing: {video.name}")
            print(f"{'='*60}")
            run_pipeline(
                input_path=str(video),
                title=args.title,
                hook_text=args.hook,
                accent_word=args.accent,
                crop_strategy=args.crop,
                upload=not args.no_upload,
                config_path=args.config,
                output_base=args.output,
                source_image=args.source_image,
                no_filter=args.no_filter,
                music_dir="" if args.no_music else args.music_dir,
                publish_at=args.publish_at,
                variants=args.variants,
            )
    elif args.input:
        run_pipeline(
            input_path=args.input,
            title=args.title,
            hook_text=args.hook,
            accent_word=args.accent,
            crop_strategy=args.crop,
            upload=not args.no_upload,
            config_path=args.config,
            output_base=args.output,
            source_image=args.source_image,
            no_filter=args.no_filter,
            music_dir="" if args.no_music else args.music_dir,
            publish_at=args.publish_at,
            variants=args.variants,
        )
    else:
        parser.print_help()
        return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())
