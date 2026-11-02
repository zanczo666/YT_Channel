#!/usr/bin/env python3
"""C2 — transkrypcja słowo po słowie (faster-whisper, CPU, int8).

Rdzeń całego montażu: czas każdego wypowiedzianego słowa. Na tym stoi C3 (dopasowanie do ID zdań
scenariusza), napisy (C8) i rozdziały (C9). Zapisuje `transcript.json` z listą słów
(`slowo`, `start`, `koniec`, `pewnosc`) oraz segmentami Whispera.

Nagranie jest dzielone na kawałki po ciszy (VAD) i każdy idzie do modelu osobno, z przesunięciem czasów.
Powód nie jest kosmetyczny: na całym pliku Whisper potrafi **milcząco pominąć początek** (test 2026-11-02:
z 36 s nagrania zjadał pierwsze 7,7 s, czyli hook, a ten sam fragment wycięty osobno transkrybował poprawnie).
Krótkie kawałki tej klasy błędów nie mają, a przy okazji granice ciszy pokrywają się z granicami ujęć.

Model: lokalnie na `claudecore` **tylko `tiny`/`base`** (7 GB RAM, bez swapu, ~1 GB wolnego — większy model
ubije sesje Claude Code). Produkcyjnie `large-v3` na workerze on-demand (docs/PIPELINE.md G3).

    ~/.venvs/whisper/bin/python scripts/transcribe.py --work /tmp/film-01 --model base
"""

from __future__ import annotations

import argparse
import json
import sys
import time
import wave
from pathlib import Path

import numpy as np

RATE = 16000


def wczytaj_wav(path: Path) -> np.ndarray:
    """WAV 16 kHz mono PCM16 → float32 w zakresie [-1, 1].

    Czytamy plik sami, zamiast dawać Whisperowi ścieżkę: jego własne dekodowanie idzie przez PyAV,
    którego API zmienia się między wersjami (av 19 nie przyjmuje już `metadata_errors`) i wywracało
    transkrypcję na zależności, a nie na dźwięku. `ingest.py` i tak zapisuje dokładnie ten format.
    """
    with wave.open(str(path), "rb") as w:
        if (w.getnchannels(), w.getsampwidth(), w.getframerate()) != (1, 2, 16000):
            sys.exit(f"błąd: {path} musi być 16 kHz mono PCM16 — przepuść nagranie przez ingest.py")
        dane = w.readframes(w.getnframes())
    return np.frombuffer(dane, dtype="<i2").astype(np.float32) / 32768.0


def pogrupuj(mowa: list[dict], dlugosc: int, max_s: float) -> list[tuple[int, int]]:
    """Odcinki mowy sklejone w kawałki nie dłuższe niż `max_s` — cięcie zawsze wypada w ciszy."""
    if not mowa:
        return [(0, dlugosc)]              # sama cisza albo VAD nic nie znalazł: oddaj całość modelowi
    limit = int(max_s * RATE)
    kawalki = [[mowa[0]["start"], mowa[0]["end"]]]
    for odcinek in mowa[1:]:
        if odcinek["end"] - kawalki[-1][0] <= limit:
            kawalki[-1][1] = odcinek["end"]
        else:
            kawalki.append([odcinek["start"], odcinek["end"]])
    return [(max(0, od), min(dlugosc, do)) for od, do in kawalki]


def main() -> None:
    ap = argparse.ArgumentParser(description="C2 — transkrypcja słowo po słowie")
    ap.add_argument("--work", required=True, type=Path, help="katalog roboczy filmu (z audio.wav)")
    ap.add_argument("--model", default="base", help="tiny | base | small | medium | large-v3 (domyślnie base)")
    ap.add_argument("--language", default="en", help="język nagrania (domyślnie en)")
    ap.add_argument("--threads", type=int, default=2, help="rdzenie CPU (domyślnie 2, żeby nie dusić serwera)")
    ap.add_argument("--max-chunk", type=float, default=25.0, help="maksymalna długość kawałka w sekundach")
    a = ap.parse_args()

    audio = a.work / "audio.wav"
    if not audio.is_file():
        sys.exit(f"błąd: brak {audio} — najpierw uruchom ingest.py")

    try:
        from faster_whisper import WhisperModel
    except ImportError:
        sys.exit("błąd: brak faster-whisper — uruchom interpreterem z venv: ~/.venvs/whisper/bin/python")

    started = time.monotonic()
    from faster_whisper.vad import VadOptions, get_speech_timestamps

    dzwiek = wczytaj_wav(audio)
    mowa = get_speech_timestamps(dzwiek, VadOptions(min_silence_duration_ms=400, speech_pad_ms=300))
    kawalki = pogrupuj(mowa, len(dzwiek), a.max_chunk)

    model = WhisperModel(a.model, device="cpu", compute_type="int8", cpu_threads=a.threads)
    slowa, segmenty = [], []
    for od, do in kawalki:
        przesuniecie = od / RATE
        segs, info = model.transcribe(
            dzwiek[od:do],
            language=a.language,
            word_timestamps=True,          # bez tego nie ma czego dopasowywać w C3
            condition_on_previous_text=False,   # powtórzone ujęcia nie mają mylić modelu kontekstem
        )
        for seg in segs:                   # generator — praca dzieje się dopiero tutaj
            segmenty.append({"start": round(seg.start + przesuniecie, 3),
                             "koniec": round(seg.end + przesuniecie, 3), "tekst": seg.text.strip()})
            for w in (seg.words or []):
                slowa.append({"slowo": w.word.strip(), "start": round(w.start + przesuniecie, 3),
                              "koniec": round(w.end + przesuniecie, 3), "pewnosc": round(w.probability, 3)})

    out = {
        "model": a.model,
        "jezyk": a.language,
        "czas_audio_s": round(len(dzwiek) / RATE, 3),
        "kawalkow": len(kawalki),
        "czas_pracy_s": round(time.monotonic() - started, 1),
        "segmenty": segmenty,
        "slowa": slowa,
    }
    (a.work / "transcript.json").write_text(json.dumps(out, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"OK: {len(slowa)} słów w {len(segmenty)} segmentach z {len(kawalki)} kawałków, "
          f"{out['czas_audio_s']:.1f} s audio w {out['czas_pracy_s']:.1f} s pracy (model {a.model})")
    print(f"     {a.work / 'transcript.json'}")


if __name__ == "__main__":
    main()
