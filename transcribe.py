from pathlib import Path
import subprocess
import argparse
import shutil
from shared import VIDEO_EXTS


def extract_audio(video_path: Path, audio_path: Path):
    cmd = [
        "ffmpeg",
        "-y",
        "-i", str(video_path),
        "-vn",
        "-acodec", "mp3",
        str(audio_path)
    ]
    subprocess.run(cmd, check=True)


def run_whisper(audio_file: Path, models_dir: Path):
    audio_dir = audio_file.parent.resolve()
    audio_name = audio_file.name

    cmd = [
        "docker", "run", "--rm",
        "-v", f"{models_dir}:/root/.cache/whisper",
        "-v", f"{audio_dir}:/app",
        "openai-whisper",
        "whisper",
        audio_name,
        "--model", "turbo",
        "--language", "Italian",
        "--output_dir", "/app",
        "--output_format", "txt"
    ]

    subprocess.run(cmd, check=True)


def transcribe_video(video_path: Path, models_dir: Path, overwrite: bool = False):
    audio_path = video_path.with_suffix(".mp3")
    txt_path = video_path.with_suffix(".txt")

    if txt_path.exists() and not overwrite:
        print(f"[SKIP] {txt_path} already exists")
        return

    print(f"[AUDIO] Extracting from {video_path.name}")
    extract_audio(video_path, audio_path)

    print(f"[WHISPER] Transcribing {audio_path.name}")
    run_whisper(audio_path, models_dir)

    # cleanup audio
    audio_path.unlink(missing_ok=True)


def main(base_dir: Path, overwrite: bool):
    models_dir = Path.cwd() / "models"
    models_dir.mkdir(exist_ok=True)

    for file in base_dir.iterdir():
        if file.is_file() and file.suffix.lower() in VIDEO_EXTS:
            transcribe_video(file, models_dir, overwrite)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("base_dir", type=str, help="Folder with video ads")
    parser.add_argument("--overwrite", action="store_true")
    args = parser.parse_args()

    main(Path(args.base_dir).resolve(), args.overwrite)
