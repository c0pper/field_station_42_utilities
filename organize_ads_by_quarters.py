from pathlib import Path
import shutil
import argparse

from ads_period_classifier_agent import agent as classifier, AdsPeriodClassifierOutputSchema, AdsPeriodClassifierInputSchema
from shared import VIDEO_EXTS, find_video_by_basename


def classify(text: str) -> str:
    """
    You plug your logic here.
    Must return one of: Q1, Q2, Q3, Q4, general
    """

    text = text.lower()
    classification: AdsPeriodClassifierOutputSchema = classifier.run(
        AdsPeriodClassifierInputSchema(transcription=text)
    )
    return classification.period

def unique_path(path: Path) -> Path:
    """
    If path exists, append _1, _2, ... before extension
    """
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

def main(base_dir: Path):
    """Moves all files from base_dir to folders by quarters"""

    txt_files = sorted(base_dir.glob("*.txt"))

    for txt_file in txt_files:
        base_name = txt_file.stem  # ad_001
        video_file = find_video_by_basename(base_dir, base_name)

        if video_file is None:
            print(f"[SKIP] {base_name} (missing video)")
            continue

        text = txt_file.read_text(encoding="utf-8")

        category = classify(text)
        if not category:
            category = "ALL_YEAR"

        target_dir = base_dir / category
        target_dir.mkdir(exist_ok=True)

        target_video_path = target_dir / video_file.name
        target_video_path = unique_path(target_video_path)

        # Move file to target dir
        # print(f"[MOVE] {base_name} -> {category}/")
        # shutil.move(str(video_file), target_video_path)

        # Copy file to target dir
        print(f"[MOVE] {base_name} -> {category}/")
        shutil.copy(str(video_file), target_video_path)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("base_dir", nargs="?", default=".")
    parser.add_argument("--overwrite", action="store_true", help="Overwrite existing merged files")
    args = parser.parse_args()

    main(Path(args.base_dir).resolve())
