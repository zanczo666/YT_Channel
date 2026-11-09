#!/usr/bin/env python3
"""G4 — retencja nagrań i monitoring dysku.

Po `retencja_dni` od publikacji usuwa surowe nagranie (inbox i kopię z Syncthinga — to ten sam plik, twarde
łącze) oraz pośrednie etapy montażu. Zostają: `final.mp4`, shorts, napisy, raporty i wszystko lekkie.
Kopię surowego nagrania masz u siebie w telefonie lub na komputerze. Przy zajętości dysku ponad próg wysyła
ostrzeżenie. `--na-sucho` tylko wypisuje.

    python3 scripts/retencja.py [--na-sucho]
"""

from __future__ import annotations

import argparse
import json
import shutil
import sys
from datetime import datetime, timedelta
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import discord  # noqa: E402

PROJEKT = Path(__file__).resolve().parent.parent
KONFIG = json.loads((PROJEKT / "config" / "kanal.json").read_text(encoding="utf-8"))
POSREDNIE = ["video.mp4", "cut.mp4", "master.mp4", "kolor.mp4", "z-grafikami.mp4", "audio.wav", "plansza.mp4",
             "intro.mp4", "czesci"]
PO_PUBLIKACJI = ("PUBLISHED", "SHORTS_SCHEDULED", "ANALYZED")
DOZWOLONE = (Path.home() / "inbox", Path.home() / "sync", Path.home() / "film")


def usun(sciezka: Path, na_sucho: bool) -> int:
    """Usuwa wyłącznie w katalogach nagrań; zwraca odzyskane bajty."""
    if not sciezka.exists() or not any(sciezka.resolve().is_relative_to(d) for d in DOZWOLONE):
        return 0
    rozmiar = sum(p.stat().st_size for p in sciezka.rglob("*") if p.is_file()) if sciezka.is_dir() else sciezka.stat().st_size
    print(f"  {'[na sucho] ' if na_sucho else ''}usuwam {sciezka} ({rozmiar / 1e6:.0f} MB)")
    if not na_sucho:
        shutil.rmtree(sciezka) if sciezka.is_dir() else sciezka.unlink()
    return rozmiar


def main() -> None:
    ap = argparse.ArgumentParser(description="G4 — retencja i dysk")
    ap.add_argument("--na-sucho", action="store_true")
    a = ap.parse_args()
    odzyskane = 0
    for p in (PROJEKT / "content" / "pipeline").glob("*/status.json"):
        st = json.loads(p.read_text(encoding="utf-8"))
        if st["stan"] not in PO_PUBLIKACJI or not st.get("publikacja"):
            continue
        if datetime.now().astimezone() < datetime.fromisoformat(st["publikacja"]) + timedelta(days=KONFIG["retencja_dni"]):
            continue
        if st.get("wideo"):
            nagranie = Path(st["wideo"])
            odzyskane += usun(nagranie, a.na_sucho)
            for kopia in (Path.home() / "sync").glob(f"*/{nagranie.name}"):
                odzyskane += usun(kopia, a.na_sucho)
        for nazwa in POSREDNIE:
            odzyskane += usun(Path.home() / "film" / st["slug"] / nazwa, a.na_sucho)
    zajetosc = shutil.disk_usage(Path.home())
    procent = 100 * zajetosc.used / zajetosc.total
    print(f"OK: odzyskano {odzyskane / 1e9:.2f} GB, dysk zajęty w {procent:.0f}%")
    if procent > KONFIG["dysk_ostrzezenie_procent"] and not a.na_sucho:
        discord.wyslij(f"Dysk claudecore zajęty w {procent:.0f}% (próg {KONFIG['dysk_ostrzezenie_procent']}%).")


if __name__ == "__main__":
    main()
