#!/usr/bin/env python3
"""C4 — lista cięć i zmontowany materiał: z `align.json` robi oś czasu, EDL i wideo bez pauz.

Bierze odcinki wybrane przez `align.py` (po jednym ujęciu na zdanie) i składa z nich jeden ciąg:
- `cut.edl` — lista montażowa CMX3600 do otwarcia w DaVinci Resolve, gdy chcesz poprawić ręcznie,
- `cut.json` — ta sama oś czasu w formie czytelnej dla kolejnych kroków (napisy C8, rozdziały C9),
- `cut.mp4` — gotowy montaż zgrubny (`--draft` = połowa rozdzielczości, szybki podgląd do akceptacji).

**Każdy odcinek renderujemy osobno, a potem sklejamy demukserem `concat`.** Pierwsza wersja budowała jeden
graf filtrów z gałęzią `trim` na odcinek — FFmpeg trzyma wtedy w pamięci tyle ścieżek dekodowania, ile jest
sklejek, i przy ośmiu odcinkach 720p wywrócił serwer (OOM, 2026-11-02). Przy filmie na ~100 zdań byłoby to
pewne niepowodzenie na każdej maszynie. Renderowanie po kawałku ma zużycie pamięci **stałe**, niezależne
od liczby sklejek.

    python3 scripts/cut.py --work /tmp/film-01 --video nagranie.mp4
"""

from __future__ import annotations

import argparse
import json
import shutil
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import proc  # noqa: E402  — wspólny limiter pamięci

FPS = 30
SZEROKOSC_DRAFT = 540


def timecode(sekundy: float, fps: int = FPS) -> str:
    """Sekundy → HH:MM:SS:KK (klatki), czyli format, którego oczekuje EDL."""
    klatki = round(sekundy * fps)
    g, reszta = divmod(klatki, 3600 * fps)
    m, reszta = divmod(reszta, 60 * fps)
    s, k = divmod(reszta, fps)
    return f"{g:02d}:{m:02d}:{s:02d}:{k:02d}"


def zapisz_edl(odcinki: list[dict], nazwa: str, path: Path, fps: int) -> None:
    """CMX3600 — najprostszy format listy montażowej, który DaVinci czyta bez pytania o wersję."""
    linie = [f"TITLE: {nazwa}", "FCM: NON-DROP FRAME", ""]
    pozycja = 0.0
    for i, o in enumerate(odcinki, 1):
        dlugosc = o["koniec"] - o["start"]
        linie += [f"{i:03d}  AX       AA/V  C        "
                  f"{timecode(o['start'], fps)} {timecode(o['koniec'], fps)} "
                  f"{timecode(pozycja, fps)} {timecode(pozycja + dlugosc, fps)}",
                  f"* FROM CLIP NAME: {o['id']}", ""]
        pozycja += dlugosc
    path.write_text("\n".join(linie), encoding="utf-8")


def renderuj_odcinek(zrodlo: Path, o: dict, cel: Path, fps: int, draft: bool, mem: str) -> None:
    """Jeden odcinek do osobnego pliku. `-ss` przed `-i` = szybkie przewijanie, a przy ponownym
    kodowaniu i tak dostajemy cięcie dokładne co do klatki."""
    skala = f",scale=-2:{SZEROKOSC_DRAFT}" if draft else ""
    proc.run(["ffmpeg", "-nostdin", "-hide_banner", "-loglevel", "error", "-y",
              "-ss", f"{o['start']:.3f}", "-t", f"{o['koniec'] - o['start']:.3f}", "-i", str(zrodlo),
              "-vf", f"fps={fps}{skala}", "-c:v", "libx264",
              "-preset", "veryfast" if draft else "medium", "-crf", "28" if draft else "18",
              "-pix_fmt", "yuv420p", "-c:a", "aac", "-b:a", "192k", "-ar", "48000", "-ac", "1",
              str(cel)], mem_max=mem, opis=f"render odcinka {o['id']}")


def main() -> None:
    ap = argparse.ArgumentParser(description="C4 — lista cięć i montaż zgrubny")
    ap.add_argument("--work", required=True, type=Path, help="katalog roboczy (z align.json)")
    ap.add_argument("--video", type=Path, help="źródło obrazu (domyślnie: zrodlo z ingest.json)")
    ap.add_argument("--draft", action="store_true", help="połowa rozdzielczości, szybki preset")
    ap.add_argument("--fps", type=int, default=FPS)
    ap.add_argument("--no-render", action="store_true", help="tylko EDL i cut.json, bez renderu")
    ap.add_argument("--mem-max", default=proc.DOMYSLNY_LIMIT,
                    help="limit pamięci na krok FFmpeg (0 = bez limitu, np. na workerze)")
    ap.add_argument("--keep-parts", action="store_true", help="zostaw pojedyncze odcinki do podglądu")
    a = ap.parse_args()

    align_path = a.work / "align.json"
    if not align_path.is_file():
        sys.exit(f"błąd: brak {align_path} — najpierw uruchom align.py")
    align = json.loads(align_path.read_text(encoding="utf-8"))
    odcinki = align["zachowaj"]
    if not odcinki:
        sys.exit("błąd: align.json nie ma ani jednego odcinka do zachowania")

    zrodlo = a.video
    if not zrodlo:
        ingest = a.work / "ingest.json"
        if not ingest.is_file():
            sys.exit("błąd: podaj --video albo uruchom najpierw ingest.py")
        zrodlo = Path(json.loads(ingest.read_text(encoding="utf-8"))["zrodlo"])
    if not zrodlo.is_file():
        sys.exit(f"błąd: nie ma pliku {zrodlo}")

    # oś czasu: gdzie każde zdanie ląduje w zmontowanym materiale (potrzebne do napisów i rozdziałów)
    os_czasu, pozycja = [], 0.0
    for o in odcinki:
        dlugosc = round(o["koniec"] - o["start"], 3)
        os_czasu.append({"id": o["id"], "zrodlo_start": o["start"], "zrodlo_koniec": o["koniec"],
                         "montaz_start": round(pozycja, 3), "montaz_koniec": round(pozycja + dlugosc, 3)})
        pozycja += dlugosc

    cut = {"zrodlo": str(zrodlo.resolve()), "fps": a.fps, "odcinkow": len(odcinki),
           "dlugosc_s": round(pozycja, 3), "os_czasu": os_czasu}
    (a.work / "cut.json").write_text(json.dumps(cut, ensure_ascii=False, indent=2), encoding="utf-8")
    zapisz_edl(odcinki, a.work.name, a.work / "cut.edl", a.fps)

    if a.no_render:
        print(f"OK: {len(odcinki)} odcinków, {pozycja:.1f} s (bez renderu)")
        print(f"     {a.work / 'cut.edl'} + {a.work / 'cut.json'}")
        return

    czesci = a.work / "czesci"
    shutil.rmtree(czesci, ignore_errors=True)
    czesci.mkdir(parents=True)
    pliki = []
    for i, o in enumerate(odcinki):
        cel = czesci / f"{i:03d}-{o['id']}.mp4"
        renderuj_odcinek(zrodlo, o, cel, a.fps, a.draft, a.mem_max)
        pliki.append(cel)

    lista = czesci / "lista.txt"
    lista.write_text("".join(f"file '{p.resolve()}'\n" for p in pliki), encoding="utf-8")
    wyjscie = a.work / ("cut-draft.mp4" if a.draft else "cut.mp4")
    proc.run(["ffmpeg", "-nostdin", "-hide_banner", "-loglevel", "error", "-y",
              "-f", "concat", "-safe", "0", "-i", str(lista), "-c", "copy", str(wyjscie)],
             mem_max=a.mem_max, opis="sklejanie odcinków")

    if not a.keep_parts:
        shutil.rmtree(czesci, ignore_errors=True)

    print(f"OK: {len(odcinki)} odcinków, {pozycja:.1f} s montażu")
    print(f"     {wyjscie} + {a.work / 'cut.edl'} + {a.work / 'cut.json'}")


if __name__ == "__main__":
    main()
