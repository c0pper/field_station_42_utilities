from pathlib import Path
import argparse
import os
import sys
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


def link_nfo_to_mtv_shows(catalog_root: Path, base_dir: Path, dry_run: bool) -> None:
    """Symlink existing NFOs from base_dir to matching videos in CATALOG_ROOT/MTV/shows"""
    mtv_shows = catalog_root / "MTV" / "shows"
    if not mtv_shows.exists():
        print(f"[SKIP] {mtv_shows} does not exist")
        return

    base_nfo_map: dict[str, Path] = {}
    for video in base_dir.rglob("*"):
        if video.is_file() and video.suffix.lower() in VIDEO_EXTS:
            nfo = video.with_suffix(".nfo")
            if nfo.exists():
                base_nfo_map[video.stem] = nfo

    mtv_videos = [
        v for v in mtv_shows.rglob("*")
        if v.is_file() and v.suffix.lower() in VIDEO_EXTS
    ]

    linked = 0
    skipped = 0
    for video in mtv_videos:
        target_nfo = video.with_suffix(".nfo")
        if target_nfo.exists():
            continue
        if video.stem in base_nfo_map:
            source_nfo = base_nfo_map[video.stem]
            if dry_run:
                print(f"[LINK] Would symlink {target_nfo} -> {source_nfo}")
            else:
                target_nfo.symlink_to(source_nfo)
                print(f"[LINK] {target_nfo} -> {source_nfo}")
            linked += 1
        else:
            if dry_run:
                print(f"[SKIP] No matching NFO for {video.stem}")
            skipped += 1

    total = len(mtv_videos)
    print(f"Done. {linked} linked, {skipped} skipped (no matching NFO), "
          f"{total - linked - skipped} already had NFOs (of {total} MTV videos)")


if __name__ == "__main__":
    if len(sys.argv) >= 2 and sys.argv[1] == "link-mtv":
        parser = argparse.ArgumentParser(
            prog="create_music_video_nfo.py link-mtv",
            description="Symlink NFOs from music videos to matching videos in MTV/shows",
        )
        parser.add_argument("--catalog-root",
                            default=os.environ.get("CATALOG_ROOT",
                                                    "/home/simo/FieldStation42/catalog"),
                            help="Catalog root directory "
                                 "(default: $CATALOG_ROOT or /home/simo/FieldStation42/catalog)")
        parser.add_argument("--base-dir",
                            default="/mnt/media_library/MusicVideos",
                            help="Music videos directory with NFOs "
                                 "(default: /mnt/media_library/MusicVideos)")
        parser.add_argument("--dry-run", action="store_true",
                            help="Preview without creating symlinks")
        args = parser.parse_args(sys.argv[2:])
        link_nfo_to_mtv_shows(
            Path(args.catalog_root).resolve(),
            Path(args.base_dir).resolve(),
            args.dry_run,
        )
    else:
        parser = argparse.ArgumentParser(description="Create NFO files for music videos")
        parser.add_argument("base_dir", nargs="?",
                            default="/mnt/media_library/MusicVideos",
                            help="Music videos directory "
                                 "(default: /mnt/media_library/MusicVideos)")
        parser.add_argument("--overwrite", action="store_true",
                            help="Overwrite existing NFO files")
        parser.add_argument("--dry-run", action="store_true",
                            help="Preview without creating files")
        parser.add_argument("--max-workers", type=int, default=4,
                            help="Parallel workers (default: 4)")
        args = parser.parse_args()

        main(Path(args.base_dir).resolve(), args.overwrite, args.dry_run, args.max_workers)
