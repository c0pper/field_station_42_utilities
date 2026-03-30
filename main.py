from pathlib import Path
import subprocess
import shutil
import argparse

TEMP_DIR = Path("/tmp/whisper_audio")


def run(cmd, check=True):
    subprocess.run(cmd, check=check)


def extract_audio(video_path: Path, output_audio: Path):
    cmd = [
        "ffmpeg",
        "-y",
        "-i", str(video_path),
        "-vn",
        "-c:a", "libmp3lame",
        str(output_audio)
    ]
    run(cmd)


def transcribe_audio(audio_path: Path, models_dir: Path):
    audio_path = audio_path.resolve()
    audio_dir = audio_path.parent
    audio_file = audio_path.name

    cmd = [
        "docker", "run", "--rm",
        "-v", f"{models_dir.resolve()}:/root/.cache/whisper",
        "-v", f"{audio_dir}:/app",
        "openai-whisper",
        "whisper", audio_file,
        "--device", "cpu",
        "--model", "turbo",
        "--language", "Italian",
        "--output_dir", "/app",
        "--output_format", "txt"
    ]

    run(cmd, check=True)


def main(base_dir: Path, models_dir: Path):
    TEMP_DIR.mkdir(parents=True, exist_ok=True)

    for folder in base_dir.iterdir():
        if not folder.is_dir():
            continue

        video_file = folder / f"{folder.name}.mp4"

        if not video_file.exists():
            print(f"[SKIP] no matching video in {folder}")
            continue

        audio_file = TEMP_DIR / f"{folder.name}.mp3"

        print(f"[AUDIO] {video_file}")
        extract_audio(video_file, audio_file)

        print(f"[WHISPER] {audio_file}")
        transcribe_audio(audio_file, models_dir)

        # Whisper writes output in same dir as audio (/app → TEMP_DIR)
        txt_file = TEMP_DIR / f"{audio_file.stem}.txt"

        if txt_file.exists():
            target = folder / txt_file.name
            shutil.move(str(txt_file), target)
            print(f"[SAVED] {target}")
        else:
            print(f"[WARN] missing transcript for {audio_file}")

    print("DONE")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("base_dir", nargs="?", default=".")
    parser.add_argument("--models-dir", required=True)

    args = parser.parse_args()

    main(
        Path(args.base_dir).resolve(),
        Path(args.models_dir).resolve()
    )
