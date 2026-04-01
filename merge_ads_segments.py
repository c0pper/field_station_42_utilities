from pathlib import Path
import subprocess
import argparse

from shared import VIDEO_EXTS


def merge_folder(folder: Path, overwrite: bool = False):
    # collect all video files
    clips = sorted([
        f for f in folder.iterdir()
        if f.is_file() and f.suffix.lower() in VIDEO_EXTS
    ])

    # optional filter
    clips = [c for c in clips if "scene-" in c.name.lower()]

    if not clips:
        print(f"[SKIP] {folder} (no clips)")
        return

    output_file = folder / f"{folder.name}.mp4"

    if output_file.exists() and not overwrite:
        print(f"[SKIP] already exists: {output_file}")
        return

    list_file = folder / "list.txt"

    # ffmpeg concat demuxer requires same codec/container
    with open(list_file, "w") as f:
        for clip in clips:
            f.write(f"file '{clip.resolve()}'\n")

    print(f"[MERGE] {folder} ({len(clips)} clips)")

    cmd = [
        "ffmpeg",
        "-y",
        "-f", "concat",
        "-safe", "0",
        "-i", str(list_file),
        "-c:v", "libx264",      # Re-encode video
        "-crf", "23",           # Quality (lower = better)
        "-preset", "fast",      # Encoding speed
        "-c:a", "aac",          # Re-encode audio
        "-b:a", "192k",         # Audio bitrate
        "-ar", "44100",         # Audio sample rate
        "-ac", "2",             # Stereo
        str(output_file)
    ]

    print(f"[MERGE] {folder}")
    subprocess.run(cmd, check=True)

    list_file.unlink(missing_ok=True)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "base_dir",
        nargs="?",
        default=".",
        help="Base directory containing ad folders (default: current directory)"
    )
    parser.add_argument(
        "--overwrite",
        action="store_true",
        help="Overwrite existing merged files"
    )
    args = parser.parse_args()

    base_dir = Path(args.base_dir).resolve()

    if not base_dir.exists():
        raise ValueError(f"Path does not exist: {base_dir}")

    print(f"[BASE DIR] {base_dir}")

    for folder in base_dir.iterdir():
        if folder.is_dir():
            merge_folder(folder, overwrite=args.overwrite)


if __name__ == "__main__":
    main()

