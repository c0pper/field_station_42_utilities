from pathlib import Path
import subprocess
import argparse


def merge_folder(folder: Path):
    clips = sorted(folder.glob("*.mp4"))

    if not clips:
        print(f"[SKIP] {folder} (no clips)")
        return

    output_file = folder / f"{folder.name}.mp4"

    # skip if already merged
    if output_file.exists():
        print(f"[SKIP] already exists: {output_file}")
        return

    list_file = folder / "list.txt"

    # create list.txt (required by ffmpeg concat demuxer)
    with open(list_file, "w") as f:
        for clip in clips:
            f.write(f"file '{clip.resolve()}'\n")

    cmd = [
        "ffmpeg",
        "-y",
        "-f", "concat",
        "-safe", "0",
        "-i", str(list_file),
        "-c", "copy",
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
    args = parser.parse_args()

    base_dir = Path(args.base_dir).resolve()

    if not base_dir.exists():
        raise ValueError(f"Path does not exist: {base_dir}")

    print(f"[BASE DIR] {base_dir}")

    for folder in base_dir.iterdir():
        if folder.is_dir():
            merge_folder(folder)


if __name__ == "__main__":
    main()

