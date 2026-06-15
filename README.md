# Field Station 42 Utilities

Python tools for downloading, processing, organizing, and enriching video advertisements and music videos. Uses AI agents (via `atomic-agents`) to classify, name, and generate metadata.

## Requirements

- Python >= 3.14
- [uv](https://docs.astral.sh/uv/) package manager
- Local OpenAI-compatible API (default: `http://127.0.0.1:1234/v1`) for AI agents
- ffmpeg, ffprobe, yt-dlp (for download/transcode tools)

## Setup

```bash
uv sync
cp .env.example .env   # configure API endpoint, key, model
```

Environment variables (see `config.py`):

| Variable | Default | Description |
|---|---|---|
| `OPENAI_BASE_URL` | `http://127.0.0.1:1234/v1` | LLM API endpoint |
| `OPENAI_API_KEY` | `ollama` | API key |
| `OPENAI_MODEL` | `qwen/qwen3.5-9b` | Model name |
| `CATALOG_ROOT` | `/home/simo/FieldStation42/catalog` | Media catalog root (used by `link-mtv`) |

## Pipeline (Ads)

The `main.py` orchestrator runs the full ad processing pipeline end-to-end:

```bash
uv run python main.py <base_folder> <ranges_file> [--overwrite]
```

Steps:
1. **Merge** scene clips into ad segments per ranges file
2. **Transcribe** each ad with Whisper (Italian)
3. **Rename** ads with descriptive names via LLM
4. **Organize** into fiscal-quarter subfolders, tagging show ads

## Scripts

### Music Video Tools

#### `create_music_video_nfo.py`

Creates `.nfo` metadata files for music videos by searching DuckDuckGo and querying an LLM agent for title, artist, album, and year. Also has a subcommand to symlink NFOs into an MTV shows catalog.

```bash
# Create NFOs
uv run python create_music_video_nfo.py [base_dir] [--overwrite] [--dry-run] [--max-workers N]

# Link NFOs to MTV/shows
uv run python create_music_video_nfo.py link-mtv [--catalog-root PATH] [--base-dir PATH] [--dry-run]
```

| Mode | Arguments | Defaults |
|---|---|---|
| `create` (default) | `base_dir` (positional, optional) | `/mnt/media_library/MusicVideos` |
| | `--overwrite` | — |
| | `--dry-run` | — |
| | `--max-workers N` | `4` |
| `link-mtv` | `--catalog-root PATH` | `$CATALOG_ROOT` or `/home/simo/FieldStation42/catalog` |
| | `--base-dir PATH` | `/mnt/media_library/MusicVideos` |
| | `--dry-run` | — |

#### `music_video_metadata_agent.py`

AI agent that identifies song metadata from a filename and DuckDuckGo search results. Used by `create_music_video_nfo.py`. Can also be run standalone:

```bash
uv run python music_video_metadata_agent.py "<query string>"
```

### Ad Pipeline Tools

#### `download_playlist.py`

Downloads videos from a hardcoded YouTube playlist (MTV commercials archive) using yt-dlp.

```bash
uv run python download_playlist.py [base_dir]
```

#### `download_and_split.py`

Downloads a single YouTube video, optionally applies cut ranges, then splits into scenes with PySceneDetect.

```bash
uv run python download_and_split.py <base_dir> <youtube_link> [--video-ranges FILE]
```

#### `merge_ads_segments.py`

Reads a scene-range file (start,end per line) and merges adjacent scene clips into `ad_NNN.mp4` files via ffmpeg concat.

```bash
uv run python merge_ads_segments.py [base_dir] <ranges_file> [--overwrite]
```

#### `transcribe.py`

Extracts audio (mp3) from video files and transcribes to Italian using a Dockerized Whisper turbo model.

```bash
uv run python transcribe.py <base_dir> [--overwrite]
```

Models are cached in `./models/`.

#### `rename_ads.py`

Renames `ad_NNN.mp4` (and matching `.txt` transcription) pairs to descriptive, filesystem-safe names using the `AdsNamingAgent`.

```bash
uv run python rename_ads.py [base_dir] [--overwrite]
```

#### `organize_ads_by_quarters.py`

Moves ad files into `Q1/` / `Q2/` / `Q3/` / `Q4/` / `ALL_YEAR/` subfolders based on LLM classification. Show ads are prefixed with `[show_ad]_`.

```bash
uv run python organize_ads_by_quarters.py [base_dir] [--overwrite]
```

### AI Agents

These agents are imported as modules by pipeline scripts. They can also be run directly for testing.

| Script | Purpose | Standalone usage |
|---|---|---|
| `ads_namer_agent.py` | Generates short, unique names for ads from transcriptions | `uv run python ads_namer_agent.py` |
| `ads_period_classifier_agent.py` | Classifies ads into fiscal quarters (Q1–Q4 / ALL_YEAR) | `uv run python ads_period_classifier_agent.py` |
| `ads_show_classifier_agent.py` | Classifies ads as show promos vs regular ads | `uv run python ads_show_classifier_agent.py` |

### Shared Utilities

#### `shared.py`

```python
VIDEO_EXTS = {".mp4", ".mkv", ".avi", ".mov", ".webm"}

find_video_by_basename(folder, base_name)  # Find first matching video in folder
unique_path(path)                           # Append _1, _2, ... if path exists
```

#### `config.py`

Loads `OPENAI_BASE_URL`, `OPENAI_API_KEY`, `OPENAI_MODEL`, and `MODEL_API_PARAMETERS` from `.env`.

## VS Code Debugging

Pre-configured launch configurations in `.vscode/launch.json`:

- **MusicVideos: Create NFOs** — `create_music_video_nfo.py --dry-run`
- **MusicVideos: Link NFOs to MTV/shows** — `create_music_video_nfo.py link-mtv --dry-run`
