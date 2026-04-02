from pathlib import Path
from typing import Optional

VIDEO_EXTS = {".mp4", ".mkv", ".avi", ".mov", ".webm"}

def find_video_by_basename(folder: Path, base_name: str) -> Optional[Path]:
    """
    Returns the first video file in the folder that matches the base_name.
    Ignores .txt files. Returns None if not found.
    """
    for f in folder.iterdir():
        if f.is_file() and f.stem == base_name and f.suffix.lower() != ".txt":
            return f
    return None


def unique_path(path: Path) -> Path:
    """If path exists, append _1, _2, ... before extension"""
    if not path.exists():
        return path

    base = path.stem
    ext = path.suffix
    parent = path.parent

    i = 1
    while True:
        candidate = parent / f"{base}_{i}{ext}"
        if not candidate.exists():
            return candidate
        i += 1