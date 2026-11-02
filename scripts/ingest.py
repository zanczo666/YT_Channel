#!/usr/bin/env python3
"""C1 — ingest nagrania: rozpoznanie pliku, audio dla transkrypcji, opcjonalna normalizacja obrazu.

Pierwszy krok montażu (docs/PIPELINE.md §3.C). Z surowego nagrania robi:
- `ingest.json` — co to za plik (długość, rozdzielczość, klatki, ścieżka audio, głośność),
- `audio.wav` — 16 kHz mono PCM, czyli format, którego oczekuje `transcribe.py`,
- `video.mp4` — opcjonalnie (`--normalize`) obraz 1080p/30 ze stałą liczbą klatek.

Normalizacja obrazu jest kosztowna i domyślnie wyłączona: do dopasowania scenariusza (C3) wystarczy audio,
a pełny przebieg i tak wykonuje worker on-demand (G3). Lokalnie na `claudecore` używaj bez `--normalize`.

    python3 scripts/ingest.py --in nagranie.mp4 --work /tmp/film-01
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path

AUDIO_RATE = 16000          # częstotliwość oczekiwana przez Whisper
TARGET_H = 1080
TARGET_FPS = 30


def run(cmd: list[str]) -> subprocess.CompletedProcess:
    """Uruchamia polecenie i przerywa z czytelnym błędem, zamiast rzucać śladem stosu."""
    res = subprocess.run(cmd, capture_output=True, text=True)
    if res.returncode != 0:
        sys.exit(f"błąd: {' '.join(cmd[:3])}… zakończyło się kodem {res.returncode}\n{res.stderr.strip()[-800:]}")
    return res


def probe(src: Path) -> dict:
    """Metadane pliku z ffprobe: strumienie i kontener."""
    res = run(["ffprobe", "-v", "error", "-print_format", "json",
               "-show_format", "-show_streams", str(src)])
    return json.loads(res.stdout)


def measure_loudness(audio: Path) -> dict | None:
    """Pomiar EBU R128 (loudnorm w trybie analizy) — punkt wyjścia do mastering u (C5)."""
    res = subprocess.run(
        ["ffmpeg", "-nostdin", "-hide_banner", "-i", str(audio),
         "-af", "loudnorm=I=-14:TP=-1.5:LRA=11:print_format=json", "-f", "null", "-"],
        capture_output=True, text=True)
    start = res.stderr.rfind("{")
    if start == -1:
        return None
    try:
        return json.loads(res.stderr[start:res.stderr.rfind("}") + 1])
    except json.JSONDecodeError:
        return None


def describe(meta: dict) -> dict:
    """Wyciąga z ffprobe tylko to, co jest nam potrzebne dalej."""
    video = next((s for s in meta["streams"] if s["codec_type"] == "video"), None)
    audio = next((s for s in meta["streams"] if s["codec_type"] == "audio"), None)
    fps = None
    if video and "/" in video.get("avg_frame_rate", ""):
        num, den = video["avg_frame_rate"].split("/")
        fps = round(int(num) / int(den), 3) if int(den) else None
    return {
        "czas_s": round(float(meta["format"]["duration"]), 3),
        "rozmiar_mb": round(int(meta["format"]["size"]) / 1024 / 1024, 1),
        "kontener": meta["format"].get("format_name"),
        "obraz": {"kodek": video["codec_name"], "szerokosc": video["width"],
                  "wysokosc": video["height"], "fps": fps} if video else None,
        "dzwiek": {"kodek": audio["codec_name"], "kanaly": audio["channels"],
                   "hz": int(audio["sample_rate"])} if audio else None,
    }


def extract_audio(src: Path, dst: Path) -> None:
    run(["ffmpeg", "-nostdin", "-hide_banner", "-loglevel", "error", "-y", "-i", str(src),
         "-vn", "-ac", "1", "-ar", str(AUDIO_RATE), "-c:a", "pcm_s16le", str(dst)])


def normalize_video(src: Path, dst: Path) -> None:
    """1080p/30 CFR — wspólny punkt wyjścia dla cięcia i renderu, niezależny od tego, czym nagrywałeś."""
    run(["ffmpeg", "-nostdin", "-hide_banner", "-loglevel", "error", "-y", "-i", str(src),
         "-vf", f"scale=-2:{TARGET_H}:flags=lanczos,fps={TARGET_FPS}",
         "-c:v", "libx264", "-preset", "medium", "-crf", "18", "-pix_fmt", "yuv420p",
         "-c:a", "aac", "-b:a", "192k", str(dst)])


def main() -> None:
    ap = argparse.ArgumentParser(description="C1 — ingest nagrania")
    ap.add_argument("--in", dest="src", required=True, type=Path, help="surowe nagranie")
    ap.add_argument("--work", required=True, type=Path, help="katalog roboczy filmu")
    ap.add_argument("--normalize", action="store_true", help="dodatkowo obraz 1080p/30 CFR (kosztowne)")
    a = ap.parse_args()

    if not a.src.is_file():
        sys.exit(f"błąd: nie ma pliku {a.src}")
    a.work.mkdir(parents=True, exist_ok=True)

    info = describe(probe(a.src))
    if not info["dzwiek"]:
        sys.exit("błąd: nagranie nie ma ścieżki dźwiękowej — bez niej nie ma transkrypcji")

    audio = a.work / "audio.wav"
    extract_audio(a.src, audio)
    info["glosnosc_wejscia"] = measure_loudness(audio)

    if a.normalize:
        normalize_video(a.src, a.work / "video.mp4")
        info["video_znormalizowane"] = "video.mp4"

    info["zrodlo"] = str(a.src.resolve())
    info["audio"] = audio.name
    (a.work / "ingest.json").write_text(json.dumps(info, ensure_ascii=False, indent=2), encoding="utf-8")

    obraz = info["obraz"]
    print(f"OK: {info['czas_s']:.1f} s, {info['rozmiar_mb']} MB"
          + (f", {obraz['szerokosc']}×{obraz['wysokosc']} @ {obraz['fps']} fps" if obraz else ", bez obrazu"))
    print(f"     {audio} + {a.work / 'ingest.json'}")


if __name__ == "__main__":
    main()
