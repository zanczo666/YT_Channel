#!/usr/bin/env python3
"""C9 — rozdziały: timestampy z rzeczywistego montażu, nie z planu w scenariuszu.

Nagłówki `## [m:ss]` w scenariuszu to szacunki pisane przed nagraniem. Po cięciu film ma inną długość,
więc do opisu idą czasy policzone z `cut.json`: rozdział zaczyna się tam, gdzie w montażu pada jego
pierwsze zdanie.

YouTube uznaje listę rozdziałów tylko wtedy, gdy pierwszy ma `0:00`, są co najmniej trzy, a każdy
trwa min. 10 s — skrypt sprawdza te trzy warunki i mówi, który nie wyszedł.

    python3 scripts/chapters.py --work /tmp/film-01 --script content/scripts/<slug>.md
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from align import czytaj_scenariusz  # noqa: E402

MIN_ROZDZIALOW = 3
MIN_DLUGOSC_S = 10.0


def znacznik(s: float) -> str:
    g, reszta = divmod(int(s), 3600)
    m, sek = divmod(reszta, 60)
    return f"{g}:{m:02d}:{sek:02d}" if g else f"{m}:{sek:02d}"


def main() -> None:
    ap = argparse.ArgumentParser(description="C9 — rozdziały z osi montażu")
    ap.add_argument("--work", required=True, type=Path, help="katalog roboczy (z cut.json)")
    ap.add_argument("--script", required=True, type=Path, help="content/scripts/<slug>.md")
    a = ap.parse_args()

    cut_path = a.work / "cut.json"
    if not cut_path.is_file():
        sys.exit(f"błąd: brak {cut_path} — najpierw uruchom cut.py")
    cut = json.loads(cut_path.read_text(encoding="utf-8"))
    rozdzialy_zdan = {z["id"]: z["rozdzial"] for z in czytaj_scenariusz(a.script)}

    rozdzialy: list[dict] = []
    for odcinek in cut["os_czasu"]:
        nazwa = rozdzialy_zdan.get(odcinek["id"])
        if not nazwa:
            continue
        if not rozdzialy or rozdzialy[-1]["nazwa"] != nazwa:
            rozdzialy.append({"nazwa": nazwa, "start": odcinek["montaz_start"]})
        rozdzialy[-1]["koniec"] = odcinek["montaz_koniec"]

    if not rozdzialy:
        sys.exit("błąd: żadne zdanie z montażu nie ma rozdziału — sprawdź nagłówki ## [m:ss] w scenariuszu")
    rozdzialy[0]["start"] = 0.0          # pierwszy rozdział musi być od zera, cokolwiek wycięliśmy na starcie

    uwagi = []
    if len(rozdzialy) < MIN_ROZDZIALOW:
        uwagi.append(f"tylko {len(rozdzialy)} rozdziały — YouTube wymaga {MIN_ROZDZIALOW}")
    for r in rozdzialy:
        if r["koniec"] - r["start"] < MIN_DLUGOSC_S:
            uwagi.append(f"„{r['nazwa']}” trwa {r['koniec'] - r['start']:.1f} s, minimum to {MIN_DLUGOSC_S:.0f} s")

    linie = [f"{znacznik(r['start'])} {r['nazwa']}" for r in rozdzialy]
    (a.work / "rozdzialy.txt").write_text("\n".join(linie) + "\n", encoding="utf-8")
    (a.work / "rozdzialy.json").write_text(
        json.dumps({"rozdzialy": rozdzialy, "uwagi": uwagi}, ensure_ascii=False, indent=2), encoding="utf-8")

    print(f"{'OK' if not uwagi else 'UWAGA'}: {len(rozdzialy)} rozdziałów, film {cut['dlugosc_s']:.1f} s")
    for u in uwagi:
        print(f"     uwaga: {u}")
    print(f"     {a.work / 'rozdzialy.txt'}")


if __name__ == "__main__":
    main()
