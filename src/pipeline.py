#!/usr/bin/env python3
"""Shorts Pipeline — convert raw video to captioned YouTube Shorts."""

import argparse
import sys


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
    args = parser.parse_args()
    print(f"Processing: {args.input}")
    print(f"Title: {args.title}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
