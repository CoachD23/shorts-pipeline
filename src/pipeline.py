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
from src.description import generate_description, save_description
from src.video import process_video, extract_frame
from src.upload import upload_video


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

    print(f"[5/6] Generating YouTube description...")
    desc_path = save_description(transcript, title, config, output_dir)

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
        "videos": video_outputs,
    }

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
            )
            result["youtube_id"] = video_id
            result["youtube_url"] = f"https://youtube.com/shorts/{video_id}"
            print(f"Uploaded: https://youtube.com/shorts/{video_id}")

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
    args = parser.parse_args()

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
        )
    else:
        parser.print_help()
        return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())
