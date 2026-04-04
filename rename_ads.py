from pathlib import Path
import argparse
import re
import unicodedata

from ads_namer_agent import agent as namer_agent, AdsNamingOutputSchema, AdsNamingInputSchema
from shared import find_video_by_basename


def sanitize(name: str) -> str:
    """
    Clean filename for filesystem
    """
    # Normalize accents: à -> a, è -> e, etc.
    name = unicodedata.normalize("NFKD", name)
    name = name.encode("ascii", "ignore").decode("ascii")
    name = name.strip().lower()
    name = re.sub(r"[^\w\s-]", "", name)
    name = re.sub(r"\s+", "_", name)
    return name[:80]  # avoid insane lengths


def namer(text: str) -> str:
    """
    Placeholder. Replace with your agent later.
    Must return a clean descriptive name.
    """

    text = text.lower()

    name: AdsNamingOutputSchema = namer_agent.run(
        AdsNamingInputSchema(transcription=text)
    )
    return name.name

def make_unique(base: str, parent: Path) -> str:
    """
    Ensure folder name is unique inside parent dir
    """
    candidate = base
    i = 1

    while (parent / candidate).exists():
        candidate = f"{base}_{i}"
        i += 1

    return candidate


def make_unique_file(base: str, folder: Path, ext: str) -> str:
    """
    Ensure filename is unique inside a folder
    """
    candidate = f"{base}{ext}"
    i = 1

    while (folder / candidate).exists():
        candidate = f"{base}_{i}{ext}"
        i += 1

    return candidate


def main(base_dir: Path):
    txt_files = sorted(base_dir.glob("*.txt"))
    if not txt_files:
        print("No .txt files found")
        return

    for txt_file in txt_files:
        base_name = txt_file.stem  # ad_001
        video_file = find_video_by_basename(base_dir, base_name)

        if video_file is None:
            print(f"[SKIP] {base_name} (missing video)")
            continue

        if not base_name.startswith(("ad_", "commercial_")):
            print(f"[SKIP] {base_name} (not an unrenamed ad)")
            continue

        text = txt_file.read_text(encoding="utf-8")

        new_base = sanitize(namer(text))

        # ensure unique base name in the SAME directory
        unique_base = new_base
        i = 1
        while (
            (base_dir / f"{unique_base}{video_file.suffix}").exists() or
            (base_dir / f"{unique_base}.txt").exists()
        ):
            unique_base = f"{new_base}_{i}"
            i += 1

        new_video = base_dir / f"{unique_base}{video_file.suffix}"
        new_txt = base_dir / f"{unique_base}.txt"

        print(f"[RENAME] {base_name} -> {unique_base}")

        video_file.rename(new_video)
        txt_file.rename(new_txt)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("base_dir", nargs="?", default=".")
    parser.add_argument("--overwrite", action="store_true", help="Overwrite existing merged files")
    args = parser.parse_args()

    main(Path(args.base_dir).resolve())
