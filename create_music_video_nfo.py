from pathlib import Path
import argparse
from concurrent.futures import ThreadPoolExecutor, as_completed
from tqdm import tqdm
from shared import VIDEO_EXTS
from music_video_metadata_agent import (
    MusicVideoMetadataAgent,
    MusicVideoMetadataInputSchema,
    search_music_video,
)


def process_one_video(video: Path, overwrite: bool) -> str:
    nfo_path = video.with_suffix(".nfo")
    if nfo_path.exists() and not overwrite:
        return f"[SKIP] {nfo_path.name} already exists"

    query = video.stem.replace("_", " ")
    results = search_music_video(query)
    if not results.strip():
        return f"[SKIP] No search results for {video.name}"

    try:
        agent = MusicVideoMetadataAgent()
        output = agent.run(
            MusicVideoMetadataInputSchema(filename=query, search_results=results)
        )
        nfo_path.write_text(
            f"{output.title}\n{output.artist}\n{output.album}\n{output.year}\n",
            encoding="utf-8"
        )
        return f"[NFO] Created {nfo_path.name}"
    except Exception as e:
        return f"[SKIP] Metadata agent failed for {video.name}: {e}"


def main(base_dir: Path, overwrite: bool, dry_run: bool, max_workers: int) -> None:
    videos = [
        v for v in base_dir.rglob("*")
        if v.is_file() and v.suffix.lower() in VIDEO_EXTS
    ]

    if dry_run:
        for video in videos:
            nfo = video.with_suffix(".nfo")
            print("[EXISTS]" if nfo.exists() else "[MISSING]", nfo.name)
        return

    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = {executor.submit(process_one_video, v, overwrite): v for v in videos}
        with tqdm(total=len(videos), desc="Creating NFOs", unit="file") as pbar:
            for future in as_completed(futures):
                pbar.write(future.result())
                pbar.update(1)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Create NFO files for music videos")
    parser.add_argument("base_dir", nargs="?", default="/mnt/media_library/MusicVideos",
                        help="Music videos directory (default: /mnt/media_library/MusicVideos)")
    parser.add_argument("--overwrite", action="store_true", help="Overwrite existing NFO files")
    parser.add_argument("--dry-run", action="store_true", help="Preview without creating files")
    parser.add_argument("--max-workers", type=int, default=4,
                        help="Parallel workers (default: 4)")
    args = parser.parse_args()

    main(Path(args.base_dir).resolve(), args.overwrite, args.dry_run, args.max_workers)
