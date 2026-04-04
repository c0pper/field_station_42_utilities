from pathlib import Path
import shutil
import argparse

from ads_period_classifier_agent import (
    agent as classifier,
    AdsPeriodClassifierOutputSchema,
    AdsPeriodClassifierInputSchema,
)
from ads_show_classifier_agent import (
    agent as show_classifier,
    AdsShowClassifierOutputSchema,
    AdsShowClassifierInputSchema,
)
from shared import VIDEO_EXTS, find_video_by_basename, unique_path


def classify(text: str, ad_name: str) -> str:
    """
    You plug your logic here.
    Must return one of: Q1, Q2, Q3, Q4, ALL_YEAR
    """

    text = text.lower()
    classification: AdsPeriodClassifierOutputSchema = classifier.run(
        AdsPeriodClassifierInputSchema(ad_name=ad_name, transcription=text)
    )
    return classification.period


def is_show_ad(text: str, ad_name: str) -> bool:
    result: AdsShowClassifierOutputSchema = show_classifier.run(
        AdsShowClassifierInputSchema(ad_name=ad_name, transcription=text)
    )
    return bool(result.is_show_ad)


def prepend_tag_if_needed(path: Path, tag: str) -> Path:
    """Prepend tag only if not already present"""
    if path.name.startswith(tag):
        return path
    return path.with_name(f"{tag}{path.name}")


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

        period = classify(text, base_name)
        if not period:
            period = "ALL_YEAR"

        show_ad = is_show_ad(text, base_name)

        target_dir = base_dir / period
        target_dir.mkdir(exist_ok=True)

        target_video_path = target_dir / video_file.name

        # Rename if show ad
        if show_ad:
            target_video_path = prepend_tag_if_needed(target_video_path, "[show_ad]_")

        target_video_path = unique_path(target_video_path)

        print(f"[MOVE] {base_name} -> {period}/ {'[show_ad]' if show_ad else ''}")
        shutil.move(str(video_file), target_video_path)

        target_txt_path = target_dir / txt_file.name
        if show_ad:
            target_txt_path = prepend_tag_if_needed(target_txt_path, "[show_ad]_")
        target_txt_path = unique_path(target_txt_path)
        shutil.move(str(txt_file), target_txt_path)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("base_dir", nargs="?", default=".")
    parser.add_argument(
        "--overwrite", action="store_true", help="Overwrite existing merged files"
    )
    args = parser.parse_args()

    main(Path(args.base_dir).resolve())
