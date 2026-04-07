#!/usr/bin/env python3
import argparse
import subprocess
from pathlib import Path


PLAYLIST_URL = (
    "https://www.youtube.com/playlist?list=PL9SMm3_hXtycQFoZ53qlJtzE9ghCDRY9D"
)


def main(base_dir: Path) -> None:
    base_dir.mkdir(parents=True, exist_ok=True)

    print(f"[PLAYLIST] {PLAYLIST_URL}")
    subprocess.run(
        [
            "yt-dlp",
            "-f",
            "bv*[height<=480]+ba/b[height<=480]",
            "-o",
            "%(playlist_index)s - %(title)s.%(ext)s",
            "--yes-playlist",
            PLAYLIST_URL,
        ],
        check=True,
        cwd=base_dir,
    )
    print(f"[DONE] Videos saved to {base_dir}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Download or update videos from a YouTube playlist."
    )
    parser.add_argument(
        "base_dir",
        type=str,
        nargs="?",
        help="Directory to save videos (default: current directory)",
        default=".",
    )
    args = parser.parse_args()

    main(Path(args.base_dir).resolve())
