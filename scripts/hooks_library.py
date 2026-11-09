#!/usr/bin/env python3
"""A5 — biblioteka haków: pierwsze sekundy filmów-outlierów niszy, rozebrane na technikę.

Bierze najlepsze odstające filmy z raportu `yt_research.py` (pole `top_outliers`) i każdy ogląda przez
`yt_watch.py` z pytaniem o pierwsze 20 s. Wynik dopisuje do `docs/research/hooks.md`; już opisane filmy pomija.

    python3 scripts/hooks_library.py --dane <raport yt_research.json> [--ile 5]
"""

from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
import tempfile
from pathlib import Path

PROJEKT = Path(__file__).resolve().parent.parent
CEL = PROJEKT / "docs" / "research" / "hooks.md"
PYTANIE = ("Look only at the first 20 seconds of this video. 1) Transcribe the spoken words verbatim. "
           "2) Describe what is on screen. 3) Name the hook technique (e.g. open loop, bold claim, contradiction, "
           "result first, question) in one line. 4) One line: how a calm, evidence-based systematic trading "
           "channel could use the same technique honestly. Answer in English, at most 150 words.")


def main() -> None:
    ap = argparse.ArgumentParser(description="A5 — biblioteka haków")
    ap.add_argument("--dane", required=True, type=Path, help="JSON z yt_research.py")
    ap.add_argument("--ile", type=int, default=5)
    a = ap.parse_args()
    raport = json.loads(a.dane.read_text(encoding="utf-8"))
    kanaly = raport if isinstance(raport, list) else raport.get("channels", [raport])
    filmy = sorted((dict(f, kanal=k.get("title", "?")) for k in kanaly for f in k.get("top_outliers", [])),
                   key=lambda f: f.get("outlier") or 0, reverse=True)
    if not CEL.is_file():
        CEL.write_text("# Biblioteka haków (A5)\n\nPierwsze 20 s filmów-outlierów niszy. Generuje "
                       "`scripts/hooks_library.py`; czyta agent `yt-scriptwriter` przy pisaniu haka.\n", encoding="utf-8")
    opisane = set(re.findall(r"youtu\.be/([\w-]{11})", CEL.read_text(encoding="utf-8")))
    dodane = 0
    for f in filmy:
        if dodane >= a.ile or f["id"] in opisane:
            continue
        with tempfile.NamedTemporaryFile("r", suffix=".md") as tmp:
            r = subprocess.run([sys.executable, str(PROJEKT / "scripts" / "yt_watch.py"), "--url",
                                f"https://youtu.be/{f['id']}", "--out", tmp.name, "--question", PYTANIE],
                               capture_output=True, text=True, timeout=2400)
            tresc = Path(tmp.name).read_text(encoding="utf-8").strip() if r.returncode == 0 else ""
        if not tresc:
            print(f"pomijam {f['id']}: {r.stderr.strip()[-200:]}")
            continue
        with CEL.open("a", encoding="utf-8") as plik:
            plik.write(f"\n## {f['title']} — {f['kanal']} (×{f.get('outlier')})\nhttps://youtu.be/{f['id']}\n\n{tresc}\n")
        dodane += 1
        print(f"dodany: {f['title'][:70]}")
    print(f"OK: {dodane} nowych haków w {CEL}")


if __name__ == "__main__":
    main()
