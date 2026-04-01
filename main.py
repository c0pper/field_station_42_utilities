from pathlib import Path
import subprocess
import re

from shared import VIDEO_EXTS
from merge_ads_segments import main as merge_ads_segments
from transcribe import transcribe_video
from rename_ads import main as rename_ads
from organize_ads_by_quarters import main as organize_ads_by_quarters

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


def main(base_folder: Path, ranges_file: Path, overwrite: bool):
    """ Merge scenes based on ranges file, transcribe ads, rename ads, organize ads by quarters """

    # merge scenes
    merge_ads_segments(base_folder, ranges_file, overwrite)
    
    # transcribe ads
    for file in base_folder.iterdir():
        if file.name.startswith("ad_") and file.suffix.lower() in VIDEO_EXTS:
            transcribe_video(file, Path.cwd() / "models", overwrite)
    
    # rename ads
    rename_ads(base_folder)

    # organize ads by quarters
    organize_ads_by_quarters(base_folder)


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument("base_folder", type=str, help="Folder containing scene files")
    parser.add_argument("ranges_file", type=str, help="Text file with scene ranges (start,end per line)")
    parser.add_argument("--overwrite", action="store_true", help="Overwrite existing merged files")
    args = parser.parse_args()

    main(Path(args.base_folder).resolve(), Path(args.ranges_file).resolve(), args.overwrite)
