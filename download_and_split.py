#!/usr/bin/env python3
import argparse
import subprocess
from pathlib import Path

from shared import VIDEO_EXTS


def find_video_file(folder: Path) -> Path | None:
    for ext in VIDEO_EXTS:
        for video_file in folder.glob(f"*{ext}"):
            return video_file
    return None


def main(base_dir: Path, youtube_link: str) -> None:
    if not base_dir.exists():
        raise ValueError(f"Base directory does not exist: {base_dir}")

    print(f"[DOWNLOAD] {youtube_link} -> {base_dir}")
    subprocess.run(
        [
            "yt-dlp",
            "-f",
            "bestvideo+bestaudio/best",
            "--merge-output-format",
            "mp4",
            "-o",
            str(base_dir / "%(title)s.%(ext)s"),
            youtube_link,
        ],
        check=True,
    )

    video_file = find_video_file(base_dir)
    if video_file is None:
        raise RuntimeError(f"Failed to find downloaded video in {base_dir}")

    print(f"[SPLIT] {video_file.name}")
    subprocess.run(
        [
            "scenedetect",
            "-i",
            str(video_file),
            "detect-content",
            "split-video",
            "-o",
            str(base_dir),
        ],
        check=True,
    )

    print(f"[DONE] Scenes saved to {base_dir}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Download a YouTube video and split it into scenes."
    )
    parser.add_argument(
        "base_dir", type=str, help="Directory to save the video and scenes"
    )
    parser.add_argument("youtube_link", type=str, help="YouTube URL to download")
    args = parser.parse_args()

    main(Path(args.base_dir).resolve(), args.youtube_link)
