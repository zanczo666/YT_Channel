#!/usr/bin/env python3
"""Uruchamianie ciężkich poleceń pod limitem pamięci (ochrona sesji Claude Code na `claudecore`).

Serwer ma 7 GB RAM, kilkanaście sesji Claude Code i **zero swapu** — proces, który urwie się z pamięcią,
nie zwalnia, tylko ubija sesje (zdarzyło się 2026-11-02 przy renderze C4). Dlatego każdy krok montażu
idzie przez `systemd-run --scope -p MemoryMax=…`: wtedy jądro zabija *nasz* proces, a nie cudzy.

Na workerze on-demand (docs/PIPELINE.md G3) limit jest zbędny — maszyna jest nasza i jednorazowa —
więc `--mem-max 0` wyłącza mechanizm.
"""

from __future__ import annotations

import shutil
import subprocess
import sys

DOMYSLNY_LIMIT = "1500M"


def limit_dostepny() -> bool:
    """Czy da się uruchomić proces w osobnej grupie kontrolnej (jest systemd i sesja użytkownika)."""
    if not shutil.which("systemd-run"):
        return False
    proba = subprocess.run(["systemd-run", "--user", "--scope", "-q", "true"],
                           capture_output=True, text=True)
    return proba.returncode == 0


def run(cmd: list[str], mem_max: str | None = DOMYSLNY_LIMIT,
        opis: str = "") -> subprocess.CompletedProcess:
    """Uruchamia polecenie; przy przekroczeniu limitu pamięci kończy z czytelnym komunikatem."""
    pelne = cmd
    if mem_max and mem_max != "0" and limit_dostepny():
        pelne = ["systemd-run", "--user", "--scope", "-q",
                 "-p", f"MemoryMax={mem_max}", "-p", "MemorySwapMax=0", *cmd]
    res = subprocess.run(pelne, capture_output=True, text=True)
    if res.returncode != 0:
        czym = opis or " ".join(cmd[:3])
        if res.returncode in (137, -9):
            sys.exit(f"błąd: {czym} przekroczyło limit pamięci {mem_max} i zostało zatrzymane.\n"
                     f"Podnieś --mem-max albo uruchom ten krok na workerze (docs/PIPELINE.md G3).")
        sys.exit(f"błąd: {czym} zakończyło się kodem {res.returncode}\n{res.stderr.strip()[-800:]}")
    return res
