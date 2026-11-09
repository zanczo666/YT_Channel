#!/usr/bin/env python3
"""E1 — raport filmu po 7 i 28 dniach z YouTube Analytics API, z utrzymaniem widza przypiętym do zdań scenariusza.

Spadek utrzymania mapujemy na ID zdania (`cut.json` z montażu), więc wniosek trafia wprost do pętli
notatek → reguł (`docs/EDITING_RULES.md`). Wyświetlenia miniatury, CTR i wyniki Test & Compare nie są
dostępne w API — raport przypomina, żeby przepisać je ze Studia.

    python3 scripts/analytics.py raport <video_id> --slug <slug> --dni 7
"""

from __future__ import annotations

import argparse
import json
import sys
from datetime import date, timedelta
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from yt_api import ANALYTICS, API, BladApi, zapytanie  # noqa: E402

PROJEKT = Path(__file__).resolve().parent.parent
METRYKI = "views,estimatedMinutesWatched,averageViewDuration,averageViewPercentage,subscribersGained,likes,comments,shares"
NAJWIEKSZE_SPADKI = 3


def raport_api(video_id: str, od: date, do: date, **parametry) -> dict:
    return zapytanie("GET", ANALYTICS, {"ids": "channel==MINE", "startDate": str(od), "endDate": str(do),
                                        "filters": f"video=={video_id}", **parametry})


def zdanie_w_czasie(cut: dict | None, sekunda: float) -> str:
    if not cut:
        return "—"
    for o in cut["os_czasu"]:
        if o["montaz_start"] <= sekunda < o["montaz_koniec"]:
            return o["id"]
    return "plansza końcowa" if sekunda >= cut["dlugosc_s"] else "—"


def main() -> None:
    ap = argparse.ArgumentParser(description="E1 — analityka filmu")
    pod = ap.add_subparsers(dest="cmd", required=True)
    p = pod.add_parser("raport")
    p.add_argument("video_id")
    p.add_argument("--slug", required=True)
    p.add_argument("--dni", type=int, default=7)
    a = ap.parse_args()
    try:
        film = zapytanie("GET", f"{API}/videos", {"part": "snippet,contentDetails", "id": a.video_id})["items"][0]
        start = date.fromisoformat(film["snippet"]["publishedAt"][:10])
        koniec = min(start + timedelta(days=a.dni), date.today())
        ogolne = raport_api(a.video_id, start, koniec, metrics=METRYKI)
        retencja = raport_api(a.video_id, start, koniec, metrics="audienceWatchRatio,relativeRetentionPerformance",
                              dimensions="elapsedVideoTimeRatio")
        zrodla = raport_api(a.video_id, start, koniec, metrics="views", dimensions="insightTrafficSourceType",
                            sort="-views")
    except BladApi as e:
        sys.exit(f"błąd: {e}")

    nazwy = [h["name"] for h in ogolne.get("columnHeaders", [])]
    wiersz = dict(zip(nazwy, (ogolne.get("rows") or [[0] * len(nazwy)])[0]))
    cut_plik = Path.home() / "film" / a.slug / "cut.json"
    cut = json.loads(cut_plik.read_text(encoding="utf-8")) if cut_plik.is_file() else None
    plansza = Path.home() / "film" / a.slug / "final.json"
    zakonczenie = json.loads(plansza.read_text()) if plansza.is_file() else {}
    intro = zakonczenie.get("intro_s", 0.0)
    dlugosc = (cut["dlugosc_s"] + zakonczenie["plansza_s"] + intro) if cut and zakonczenie else None
    punkty = [(r[0], r[1], r[2]) for r in retencja.get("rows", [])]
    spadki = sorted(((punkty[i][1] - punkty[i + 1][1], punkty[i + 1][0]) for i in range(len(punkty) - 1)),
                    reverse=True)[:NAJWIEKSZE_SPADKI]

    linie = [f"# Analityka: {a.slug} — {a.dni} dni", "", f"Film: https://youtu.be/{a.video_id}, okres {start} – {koniec}.", "",
             "| Metryka | Wartość |", "|---|---|"]
    linie += [f"| {k} | {v} |" for k, v in wiersz.items()]
    linie += ["", "## Największe spadki utrzymania", "",
              "| Moment | Spadek | Zdanie |", "|---|---|---|"]
    for spadek, ulamek in spadki:
        sek = ulamek * dlugosc if dlugosc else None
        linie.append(f"| {ulamek:.0%}" + (f" ({int(sek // 60)}:{int(sek % 60):02d})" if sek else "")
                     + f" | {spadek:.1%} | {zdanie_w_czasie(cut, sek - intro) if sek else '—'} |")
    linie += ["", "## Źródła ruchu", "", "| Źródło | Wyświetlenia |", "|---|---|"]
    linie += [f"| {r[0]} | {r[1]} |" for r in zrodla.get("rows", [])]
    linie += ["", "## Do uzupełnienia ze Studia", "",
              "- Wyświetlenia miniatury i CTR (niedostępne w API).", "- Wynik Test & Compare (zwycięska miniatura).",
              "", "## Wnioski", "",
              "Dla każdego spadku wskaż regułę, która by mu zapobiegła, i dopisz ją do `docs/EDITING_RULES.md`."]
    cel = PROJEKT / "content" / "analytics" / f"{a.slug}-{a.dni}d.md"
    cel.parent.mkdir(parents=True, exist_ok=True)
    cel.write_text("\n".join(linie) + "\n", encoding="utf-8")
    print(f"OK: {cel}")


if __name__ == "__main__":
    main()
