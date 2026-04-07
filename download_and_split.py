#!/usr/bin/env python3
import argparse
import re
import subprocess
import tempfile
from pathlib import Path

from shared import VIDEO_EXTS

RANGE_PATTERN = re.compile(
    r"^(\d{1,2}:\d{2}(?::\d{2})?)\s*,\s*(\d{1,2}:\d{2}(?::\d{2})?)$"
)


def parse_ranges_file(path: Path) -> list[tuple[str, str]]:
    ranges: list[tuple[str, str]] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line:
            continue
        match = RANGE_PATTERN.match(line)
        if not match:
            raise ValueError(f"Invalid range format: {line!r}")
        ranges.append((match.group(1), match.group(2)))
    return ranges


def find_video_file(folder: Path) -> Path | None:
    for ext in VIDEO_EXTS:
        for video_file in folder.glob(f"*{ext}"):
            return video_file
    return None


def cut_video(video_path: Path, ranges: list[tuple[str, str]], temp_dir: Path) -> Path:
    clips: list[Path] = []
    for i, (start, end) in enumerate(ranges):
        clip_path = temp_dir / f"clip_{i:03d}.mp4"
        subprocess.run(
            [
                "ffmpeg",
                "-y",
                "-ss",
                start,
                "-to",
                end,
                "-i",
                str(video_path),
                "-c",
                "copy",
                str(clip_path),
            ],
            check=True,
            capture_output=True,
        )
        clips.append(clip_path)

    concat_file = temp_dir / "concat.txt"
    concat_file.write_text(
        "\n".join(f"file '{c}'" for c in clips),
        encoding="utf-8",
    )

    output_path = video_path
    subprocess.run(
        [
            "ffmpeg",
            "-y",
            "-f",
            "concat",
            "-safe",
            "0",
            "-i",
            str(concat_file),
            "-c",
            "copy",
            str(output_path),
        ],
        check=True,
        capture_output=True,
    )
    return output_path


def main(base_dir: Path, youtube_link: str, ranges_path: Path | None) -> None:
    if not base_dir.exists():
        raise ValueError(f"Base directory does not exist: {base_dir}")

    print(f"[DOWNLOAD] {youtube_link} -> {base_dir}")
    subprocess.run(
        [
            "yt-dlp",
            "-f",
            "bestvideo+bestaudio/best",
            # "--merge-output-format",
            # "mp4",
            "-o",
            str(base_dir / "%(title)s.%(ext)s"),
            youtube_link,
        ],
        check=True,
    )

    video_file = find_video_file(base_dir)
    if video_file is None:
        raise RuntimeError(f"Failed to find downloaded video in {base_dir}")

    if ranges_path is not None:
        ranges = parse_ranges_file(ranges_path)
        print(f"[CUT] Extracting {len(ranges)} range(s) from {video_file.name}")
        with tempfile.TemporaryDirectory() as temp_dir:
            video_file = cut_video(video_file, ranges, Path(temp_dir))
        print(f"[CUT] Reassembled video: {video_file.name}")

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
    parser.add_argument(
        "--video-ranges",
        type=str,
        help="Path to file with time ranges (MM:SS,MM:SS format, one per line)",
        default=None,
    )
    args = parser.parse_args()

    ranges_path = Path(args.video_ranges) if args.video_ranges else None
    main(Path(args.base_dir).resolve(), args.youtube_link, ranges_path)
