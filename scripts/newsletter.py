#!/usr/bin/env python3
"""E3 — szkic miesięcznego newslettera: raport lejka z karty fabryki i filmy z ostatniego miesiąca.

Liczby wyłącznie z karty `context/factory/funnel/…` (bez karty szkic mówi o tym wprost, zamiast zgadywać).
Wynik to szkic do akceptacji w `content/newsletter/RRRR-MM.md`; wysyłkę robi właściciel w swoim narzędziu.

    python3 scripts/newsletter.py [--miesiac RRRR-MM]
"""

from __future__ import annotations

import argparse
import json
import sys
from datetime import date
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import agent  # noqa: E402

PROJEKT = Path(__file__).resolve().parent.parent


def main() -> None:
    ap = argparse.ArgumentParser(description="E3 — szkic newslettera")
    ap.add_argument("--miesiac", default=f"{date.today():%Y-%m}")
    a = ap.parse_args()
    karty = sorted((PROJEKT / "context" / "factory").glob("funnel*/**/*.md")) + \
        sorted((PROJEKT / "context" / "factory").glob("*funnel*.md"))
    filmy = [json.loads(p.read_text()) for p in (PROJEKT / "content" / "pipeline").glob("*/status.json")]
    opublikowane = [f for f in filmy if (f.get("publikacja") or "").startswith(a.miesiac)]
    cel = PROJEKT / "content" / "newsletter" / f"{a.miesiac}.md"
    cel.parent.mkdir(parents=True, exist_ok=True)
    zrodla = "\n".join(f"- {k.relative_to(PROJEKT)}" for k in karty[-2:]) or "- brak karty lejka"
    filmy_txt = "\n".join(f"- {f['slug']} (https://youtu.be/{f.get('yt_id', '?')})" for f in opublikowane) or "- brak"
    ok, odp = agent.uruchom(
        f"Napisz szkic newslettera za {a.miesiac} po angielsku do pliku {cel.relative_to(PROJEKT)}. "
        f"Źródła liczb (wyłącznie te karty, bez szacunków):\n{zrodla}\nFilmy z tego miesiąca:\n{filmy_txt}\n"
        "Układ: 1) lejek miesiąca (ile hipotez, gdzie odpadły — tylko z karty; bez karty napisz, że raport "
        "lejka w tym miesiącu się nie ukazał), 2) filmy miesiąca, 3) jedna lekcja. Bez języka sprzedaży, "
        "z zastrzeżeniem o wynikach historycznych. Na górze komentarz HTML: SZKIC DO AKCEPTACJI.", "newsletter")
    if not ok or not cel.is_file():
        sys.exit(f"błąd: agent nie przygotował szkicu: {odp[-300:]}")
    print(f"OK: {cel}")


if __name__ == "__main__":
    main()
