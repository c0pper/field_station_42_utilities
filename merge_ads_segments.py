from pathlib import Path
import re
import shutil
import subprocess
import argparse

from shared import VIDEO_EXTS


def merge_scenes(base_folder: Path, start_scene: int, end_scene: int, ad_index: int, overwrite: bool = False):
    """
    Merge scene files for a single ad based on scene numbers.
    Output filename is progressive: ad_001.mp4, ad_002.mp4, etc.
    """
    # Collect all scene files
    scene_files = sorted([
        f for f in base_folder.iterdir()
        if f.is_file() and f.suffix.lower() in VIDEO_EXTS
    ])

    # Filter scenes for this ad
    clips = [
        f for f in scene_files
        if start_scene <= extract_scene_number(f.name) <= end_scene
    ]

    if not clips:
        print(f"[SKIP] No scenes found for ad {ad_index} ({start_scene}-{end_scene})")
        return

    output_file = base_folder / f"ad_{ad_index:03d}.mp4"

    if output_file.exists() and not overwrite:
        print(f"[SKIP] {output_file} already exists. Use overwrite=True to replace.")
        return

    # --- SINGLE CLIP CASE ---
    if len(clips) == 1:
        print(f"[COPY] ad_{ad_index:03d} (single clip)")

        if overwrite or not output_file.exists():
            shutil.copy(str(clips[0]), output_file)

        return

    list_file = base_folder / f"ad_{ad_index:03d}_list.txt"
    with open(list_file, "w") as f:
        for clip in clips:
            f.write(f"file '{clip.resolve()}'\n")

    cmd = [
        "ffmpeg",
        "-y" if overwrite else "-n",
        "-f", "concat",
        "-safe", "0",
        "-i", str(list_file),
        "-c:v", "libx264",
        "-crf", "23",
        "-preset", "fast",
        "-c:a", "aac",
        "-b:a", "192k",
        "-ar", "44100",
        "-ac", "2",
        str(output_file)
    ]

    print(f"[MERGE] ad_{ad_index:03d} ({len(clips)} clips)")
    subprocess.run(cmd, check=True)
    list_file.unlink(missing_ok=True)


def extract_scene_number(filename: str) -> int:
    """Extract scene number from filename, expects 'scene-N'."""
    m = re.search(r"scene-(\d+)", filename.lower())
    return int(m.group(1)) if m else -1


def read_ranges(file_path: Path):
    """Read start/end scene ranges from a file. Returns list of (start, end) tuples."""
    ranges = []
    with open(file_path, "r") as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            parts = line.split(",")
            if len(parts) != 2:
                continue
            start, end = map(int, parts)
            ranges.append((start, end))
    return ranges


def main(base_dir: Path, ranges_file: Path, overwrite: bool):
    """ Merge scenes based on ranges file """
    scene_ranges = read_ranges(ranges_file)

    # merge scenes
    for i, (start, end) in enumerate(scene_ranges, start=1):
        merge_scenes(base_dir, start, end, ad_index=i, overwrite=overwrite)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "base_dir",
        nargs="?",
        default=".",
        help="Base directory containing ad folders (default: current directory)"
    )
    parser.add_argument(
        "ranges_file", 
        type=str, 
        help="Text file with scene ranges (start,end per line)"
    )
    parser.add_argument(
        "--overwrite",
        action="store_true",
        help="Overwrite existing merged files"
    )
    args = parser.parse_args()

    base_dir = Path(args.base_dir).resolve()
    ranges_file = Path(args.ranges_file).resolve()

    if not base_dir.exists():
        raise ValueError(f"Path does not exist: {base_dir}")

    print(f"[BASE DIR] {base_dir}")

    main(base_dir, ranges_file, args.overwrite)

