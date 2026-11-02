#!/usr/bin/env python3
"""Sztuczne nagranie próbne do testów pipeline'u C1–C5 — bez udziału właściciela.

Prawdziwe nagranie jest po stronie właściciela i do testów regresyjnych i tak by się nie nadawało:
za każdym razem brzmi inaczej. Tutaj mowa idzie z syntezatora (`espeak-ng`), więc test jest
powtarzalny i można go odtworzyć na każdej maszynie — również na świeżym workerze.

Nagranie celowo zawiera to, co pipeline ma umieć obsłużyć:
- zdanie powtórzone po pomyłce (L003) — C3 ma wybrać **ujęcie późniejsze**, a wcześniejsze wyciąć,
- urwane ujęcie z komentarzem „let me say that again” — nie należy do scenariusza, ma zniknąć,
- ciszę między ujęciami — C2 tnie po niej dźwięk na kawałki, C4 wycina ją z taśmy.

    python3 scripts/nagranie_probne.py --out /tmp/film-test
"""

from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path

GLOS = "en-us"
TEMPO = 150          # słów na minutę — wolniej niż domyślne 175, Whisper ma łatwiej
PRZERWA = 0.6        # cisza między ujęciami (s); C2 tnie właśnie po ciszy
PRZERWA_PO_WPADCE = 1.2   # dłuższa pauza po pomyłce — tak to wygląda przy prawdziwym nagrywaniu

# (ID zdania albo None dla ujęcia do wyrzucenia, tekst wypowiadany)
UJECIA = [
    ("L001", "Most backtests that look great never survive a single honest test."),
    ("L002", "In this video I run that test, and I show you the result either way."),
    (None,   "The first thing we check is whether the... no, let me say that again."),
    ("L003", "The first thing we check is whether the edge holds out of sample."),
    ("L004", "I split the data into two halves and I never touch the second one."),
    ("L005", "The strategy made money in sample and lost money out of sample."),
    ("L006", "That gap is the whole story, and it is the most common failure I see."),
    ("L007", "You can run the same split on your own system in about ten minutes."),
    ("L008", "Historical results, not investment advice. Past performance does not guarantee future results."),
]

SCENARIUSZ = """---
slug: _test-pipeline
filar: Validation Gates
zrodlo: nagranie syntetyczne (scripts/nagranie_probne.py)
publish_after: brak
tytul_roboczy: Out of sample split — test nagrania próbnego
dlugosc_docelowa: 1 min
slowa_szacunkowo: 90
---

> **Nie do publikacji.** Plik testowy pipeline'u montażu; generuje go `scripts/nagranie_probne.py`.

## [0:00] Hook
| ID | EN (mówione) | PL (napisy) | Na ekranie |
|---|---|---|---|
| L001 | Most backtests that look great never survive a single honest test. | Większość świetnie wyglądających backtestów nie przeżywa jednego uczciwego testu. | TWARZ |
| L002 | In this video I run that test, and I show you the result either way. | W tym filmie przeprowadzam ten test i pokazuję wynik niezależnie od tego, jaki wyjdzie. | TWARZ |

## [~0:15] What happened
| ID | EN (mówione) | PL (napisy) | Na ekranie |
|---|---|---|---|
| L003 | The first thing we check is whether the edge holds out of sample. | Najpierw sprawdzamy, czy przewaga utrzymuje się poza próbą. | EKRAN: podział danych |
| L004 | I split the data into two halves and I never touch the second one. | Dzielę dane na dwie połowy i drugiej nigdy nie dotykam. | EKRAN: podział danych |
| L005 | The strategy made money in sample and lost money out of sample. | Strategia zarabiała w próbie i traciła poza próbą. | GRAFIKA: equity IS/OOS |

## [~0:35] Why it matters to you
| ID | EN (mówione) | PL (napisy) | Na ekranie |
|---|---|---|---|
| L006 | That gap is the whole story, and it is the most common failure I see. | Ta różnica to cała historia i najczęstsza porażka, jaką widuję. | TWARZ |
| L007 | You can run the same split on your own system in about ten minutes. | Ten sam podział możesz zrobić u siebie w jakieś dziesięć minut. | EKRAN: kod |

## [~0:50] Disclaimer
| ID | EN (mówione) | PL (napisy) | Na ekranie |
|---|---|---|---|
| L008 | Historical results, not investment advice. Past performance does not guarantee future results. | Wyniki historyczne, nie porada inwestycyjna. Wyniki z przeszłości nie gwarantują przyszłych. | TWARZ |
"""


def mowa(tekst: str, cel: Path) -> None:
    subprocess.run(["espeak-ng", "-v", GLOS, "-s", str(TEMPO), "-w", str(cel), tekst], check=True)


def cisza(sekundy: float, cel: Path) -> None:
    subprocess.run(["ffmpeg", "-y", "-v", "error", "-f", "lavfi",
                    "-i", f"anullsrc=r=22050:cl=mono", "-t", f"{sekundy}", str(cel)], check=True)


def main() -> None:
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--out", type=Path, required=True, help="katalog na nagranie")
    p.add_argument("--script", type=Path, default=Path("content/scripts/_test-pipeline.md"))
    a = p.parse_args()

    for narzedzie in ("espeak-ng", "ffmpeg"):
        if subprocess.run(["which", narzedzie], capture_output=True).returncode != 0:
            sys.exit(f"błąd: brak {narzedzie}")

    a.out.mkdir(parents=True, exist_ok=True)
    a.script.parent.mkdir(parents=True, exist_ok=True)
    a.script.write_text(SCENARIUSZ, encoding="utf-8")

    czesci, tmp = [], a.out / "_tmp"
    tmp.mkdir(exist_ok=True)
    poprzednie_bylo_wpadka = False
    for i, (ident, tekst) in enumerate(UJECIA):
        przerwa = tmp / f"{i:02d}-cisza.wav"
        cisza(PRZERWA_PO_WPADCE if poprzednie_bylo_wpadka else PRZERWA, przerwa)
        czesci.append(przerwa)
        glos = tmp / f"{i:02d}-glos.wav"
        mowa(tekst, glos)
        czesci.append(glos)
        poprzednie_bylo_wpadka = ident is None
    koniec = tmp / "99-cisza.wav"
    cisza(PRZERWA, koniec)
    czesci.append(koniec)

    lista = tmp / "lista.txt"
    lista.write_text("".join(f"file '{c.resolve()}'\n" for c in czesci), encoding="utf-8")
    dzwiek = tmp / "sciezka.wav"
    subprocess.run(["ffmpeg", "-y", "-v", "error", "-f", "concat", "-safe", "0", "-i", str(lista),
                    "-ar", "22050", "-ac", "1", str(dzwiek)], check=True)

    # obraz: testsrc2 — deterministyczny i widać na nim, czy cięcie wypadło tam, gdzie miało
    film = a.out / "nagranie-probne.mp4"
    subprocess.run(["ffmpeg", "-y", "-v", "error",
                    "-f", "lavfi", "-i", "testsrc2=size=1280x720:rate=30",
                    "-i", str(dzwiek), "-shortest",
                    "-c:v", "libx264", "-preset", "veryfast", "-pix_fmt", "yuv420p",
                    "-c:a", "aac", "-b:a", "128k", str(film)], check=True)

    dlugosc = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration",
                              "-of", "csv=p=0", str(film)], capture_output=True, text=True).stdout.strip()
    zdania = [i for i, _ in UJECIA if i]
    print(f"nagranie: {film} ({float(dlugosc):.1f} s)")
    print(f"scenariusz: {a.script} ({len(zdania)} zdań: {', '.join(zdania)})")
    print("oczekiwane: L003 z ujęcia drugiego, urwane ujęcie i cisza na liście do wycięcia")


if __name__ == "__main__":
    main()
