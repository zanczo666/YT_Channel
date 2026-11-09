#!/usr/bin/env python3
"""E2 — dzienny przegląd komentarzy z propozycjami odpowiedzi; odpowiedź idzie dopiero po akceptacji.

`przeglad` zbiera nowe komentarze ze wszystkich wgranych filmów do `content/comments/<data>.md`, a agent
dopisuje pod każdym propozycję odpowiedzi (granice kanału jak w scenariuszach: bez sprzedaży, bez porad
inwestycyjnych). Wysłanie odpowiedzi to osobne, ręczne polecenie `odpowiedz`.

    python3 scripts/komentarze.py [przeglad]
    python3 scripts/komentarze.py odpowiedz <comment_id> "treść"
"""

from __future__ import annotations

import json
import sys
from datetime import date
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import agent  # noqa: E402
from yt_api import API, BladApi, zapytanie  # noqa: E402

PROJEKT = Path(__file__).resolve().parent.parent
WIDZIANE = PROJEKT / "content" / "pipeline" / "_komentarze.json"


def przeglad() -> None:
    widziane = set(json.loads(WIDZIANE.read_text())) if WIDZIANE.is_file() else set()
    filmy = [json.loads(p.read_text()) for p in (PROJEKT / "content" / "pipeline").glob("*/status.json")]
    nowe = []
    for st in (f for f in filmy if f.get("yt_id")):
        odp = zapytanie("GET", f"{API}/commentThreads", {"part": "snippet", "videoId": st["yt_id"],
                                                         "maxResults": 100, "order": "time", "textFormat": "plainText"})
        for w in odp.get("items", []):
            if w["id"] not in widziane:
                k = w["snippet"]["topLevelComment"]["snippet"]
                nowe.append((st["slug"], w["id"], k["authorDisplayName"], k["textDisplay"]))
                widziane.add(w["id"])
    if not nowe:
        print("OK: brak nowych komentarzy")
        return
    cel = PROJEKT / "content" / "comments" / f"{date.today()}.md"
    cel.parent.mkdir(parents=True, exist_ok=True)
    linie = [f"# Komentarze {date.today()}", "",
             "Odpowiedź wysyłasz poleceniem `python3 scripts/komentarze.py odpowiedz <ID> \"treść\"`.", ""]
    for slug, cid, autor, tekst in nowe:
        linie += [f"## {slug} — {autor}", f"ID: `{cid}`", "", f"> {tekst}", "", "Propozycja odpowiedzi: _(agent)_", ""]
    cel.write_text("\n".join(linie), encoding="utf-8")
    agent.uruchom(f"W pliku {cel.relative_to(PROJEKT)} pod każdym komentarzem zastąp „_(agent)_” propozycją krótkiej "
                  "odpowiedzi po angielsku, spokojnej i rzeczowej, zgodnej z granicami z CLAUDE.md (bez sprzedaży, bez "
                  "porad inwestycyjnych, bez obietnic wyników). Spam i hejt oznacz „pomiń”.", "komentarze")
    WIDZIANE.write_text(json.dumps(sorted(widziane)), encoding="utf-8")
    print(f"OK: {len(nowe)} nowych → {cel}")


def odpowiedz(cid: str, tekst: str) -> None:
    zapytanie("POST", f"{API}/comments", {"part": "snippet"},
              {"snippet": {"parentId": cid, "textOriginal": tekst}})
    print("OK: odpowiedź wysłana")


if __name__ == "__main__":
    try:
        if sys.argv[1:2] in ([], ["przeglad"]):
            przeglad()
        elif sys.argv[1:2] == ["odpowiedz"] and len(sys.argv) == 4:
            odpowiedz(sys.argv[2], sys.argv[3])
        else:
            sys.exit(__doc__)
    except BladApi as e:
        sys.exit(f"błąd: {e}")
