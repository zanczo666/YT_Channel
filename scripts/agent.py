#!/usr/bin/env python3
"""G6 — agenci Claude Code bez czatu: `claude -p` wywoływany przez runner.

Agent dostaje komendę projektu (np. `/scenariusz`, `/publikacja`, `/pomysly`) i pracuje w katalogu projektu
z wąskim zestawem narzędzi: czyta repo, pisze w `content/`, uruchamia skrypty kontrolne. Nie commituje,
nie wysyła niczego na zewnątrz: zmiany zatwierdza runner, a treść właściciel na bramce.

    python3 scripts/agent.py "/pomysly"
"""

from __future__ import annotations

import subprocess
import sys
from datetime import datetime
from pathlib import Path

PROJEKT = Path(__file__).resolve().parent.parent
LOGI = PROJEKT / "content" / "pipeline" / "_agenci"
NARZEDZIA = ["Read", "Write", "Edit", "Glob", "Grep", "Task", "Agent",
             "Bash(python3 scripts/compliance.py:*)", "Bash(python3 scripts/thumbnail.py:*)",
             "Bash(python3 scripts/thumbnail_grid.py:*)", "Bash(wc:*)", "Bash(ls:*)", "Bash(grep:*)"]
LIMIT_S = 3600


def uruchom(polecenie: str, opis: str = "agent", limit_s: int = LIMIT_S) -> tuple[bool, str]:
    """Zwraca (powodzenie, ostatnia część odpowiedzi). Pełny zapis trafia do content/pipeline/_agenci/."""
    LOGI.mkdir(parents=True, exist_ok=True)
    log = LOGI / f"{datetime.now():%Y%m%d-%H%M%S}-{opis}.log"
    try:
        res = subprocess.run(["claude", "-p", polecenie, "--permission-mode", "acceptEdits",
                              "--allowedTools", ",".join(NARZEDZIA)],
                             cwd=PROJEKT, capture_output=True, text=True, timeout=limit_s)
    except FileNotFoundError:
        return False, "brak polecenia `claude` w PATH"
    except subprocess.TimeoutExpired:
        log.write_text(f"$ {polecenie}\n\nprzekroczony limit {limit_s} s\n", encoding="utf-8")
        return False, f"przekroczony limit {limit_s} s"
    log.write_text(f"$ {polecenie}\n\n{res.stdout}\n--- stderr ---\n{res.stderr}", encoding="utf-8")
    return res.returncode == 0, (res.stdout or res.stderr).strip()[-1500:]


if __name__ == "__main__":
    if len(sys.argv) != 2:
        sys.exit(__doc__)
    ok, odp = uruchom(sys.argv[1])
    print(odp)
    sys.exit(0 if ok else 1)
