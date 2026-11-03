#!/usr/bin/env python3
"""B3 — odbiór nagrań: z folderów Syncthinga do `inbox/`, dopiero gdy plik jest kompletny.

Syncthing trzyma swoje foldery w `~/sync/<źródło>` (telefon, komputer). Pipeline oczekuje nagrań
w `~/inbox/` i nic poza tym skryptem nie zagląda do `~/sync` — dzięki temu Syncthing i montaż
nigdy nie walczą o te same pliki.

Dlaczego nie da się po prostu obserwować `inbox/`:
- **plik w trakcie przesyłu** — Syncthing pisze do `.syncthing.<nazwa>.tmp` i zmienia nazwę na
  docelową dopiero po komplecie, więc sama nazwa docelowa zwykle znaczy „gotowe”,
- **ale nie zawsze** — na komputerze OBS pisze prosto do folderu synchronizowanego, więc Syncthing
  przesyła plik, który wciąż rośnie; po stronie serwera widać wtedy niepełne nagranie pod docelową nazwą.
Dlatego warunkiem odbioru jest **niezmienny rozmiar i czas modyfikacji** przez `STABILNE_S`;
skrypt chodzi z timera co minutę, więc nagranie trafia do `inbox/` chwilę po tym, jak przestanie rosnąć.

Przeniesienie to **twarde łącze** (`os.link`), nie kopia: ten sam system plików, więc jest natychmiastowe
i nie zajmuje drugi raz miejsca. Usunięcie nagrania w telefonie zabiera plik z `~/sync`, a łącze
w `inbox/` zostaje — materiał źródłowy nie znika nam z serwera przez porządki w galerii.

    python3 scripts/odbierz.py            # jeden przebieg (tak woła timer)
    python3 scripts/odbierz.py --sucho    # tylko pokaż, co by zrobił
"""

from __future__ import annotations

import argparse
import json
import os
import shutil
import sys
import time
from datetime import datetime
from pathlib import Path

ZRODLA = Path("/home/claude/sync")
INBOX = Path("/home/claude/inbox")
STAN = Path("/home/claude/.local/state/yt_channel/odbierz.json")
LOG = Path("/home/claude/.local/state/yt_channel/odbierz.log")

STABILNE_S = 45.0          # tyle plik musi być niezmienny, żeby uznać go za kompletny
MIN_ROZMIAR = 1_000_000    # poniżej 1 MB to nie nagranie, a pomyłka albo miniatura
ROZSZERZENIA = {".mp4", ".mov", ".mkv", ".m4v", ".avi", ".wav", ".m4a"}
POMIJAJ = (".syncthing.", "~syncthing~", ".stfolder", ".stignore", ".stversions")


def loguj(tekst: str) -> None:
    LOG.parent.mkdir(parents=True, exist_ok=True)
    with LOG.open("a", encoding="utf-8") as f:
        f.write(f"{datetime.now():%Y-%m-%d %H:%M:%S} {tekst}\n")
    print(tekst)


def czytaj_stan() -> dict:
    if not STAN.is_file():
        return {"obserwowane": {}, "odebrane": {}}
    try:
        return json.loads(STAN.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        # uszkodzony stan nie może blokować odbioru — zaczynamy obserwację od nowa
        loguj("uwaga: stan nieczytelny, zaczynam od zera")
        return {"obserwowane": {}, "odebrane": {}}


def zapisz_stan(stan: dict) -> None:
    STAN.parent.mkdir(parents=True, exist_ok=True)
    tmp = STAN.with_suffix(".json.tmp")
    tmp.write_text(json.dumps(stan, ensure_ascii=False, indent=2), encoding="utf-8")
    tmp.replace(STAN)


def kandydaci() -> list[Path]:
    if not ZRODLA.is_dir():
        return []
    out = []
    for p in sorted(ZRODLA.rglob("*")):
        if not p.is_file() or p.is_symlink():
            continue
        if any(cz.startswith(POMIJAJ) for cz in p.parts):
            continue
        if p.suffix.lower() not in ROZSZERZENIA:
            continue
        out.append(p)
    return out


def wolna_nazwa(nazwa: str, rozmiar: int) -> Path | None:
    """Cel w `inbox/`. `None`, gdy taki plik już tam jest (ten sam rozmiar = ten sam materiał)."""
    cel = INBOX / nazwa
    if not cel.exists():
        return cel
    if cel.stat().st_size == rozmiar:
        return None
    for i in range(2, 100):
        alt = INBOX / f"{Path(nazwa).stem}-{i}{Path(nazwa).suffix}"
        if not alt.exists():
            return alt
    return None


def przenies(src: Path, cel: Path) -> None:
    """Twarde łącze; kopia tylko wtedy, gdy źródło leży na innym systemie plików."""
    try:
        os.link(src, cel)
    except OSError:
        shutil.copy2(src, cel)


def main() -> None:
    ap = argparse.ArgumentParser(description="B3 — odbiór nagrań z Syncthinga do inbox/")
    ap.add_argument("--sucho", action="store_true", help="nic nie przenoś, tylko pokaż decyzje")
    ap.add_argument("--stabilne", type=float, default=STABILNE_S,
                    help="ile sekund plik musi być niezmienny (domyślnie %(default)s)")
    a = ap.parse_args()

    if not INBOX.is_dir():
        sys.exit(f"błąd: nie ma {INBOX}")

    stan = czytaj_stan()
    obserwowane, odebrane = stan["obserwowane"], stan["odebrane"]
    teraz = time.time()
    widziane, nowe = set(), 0

    for p in kandydaci():
        klucz = str(p.relative_to(ZRODLA))
        st = p.stat()
        odcisk = f"{st.st_size}:{int(st.st_mtime)}"
        widziane.add(klucz)

        if odebrane.get(klucz) == odcisk:
            continue
        if st.st_size < MIN_ROZMIAR:
            continue

        wpis = obserwowane.get(klucz)
        if not wpis or wpis["odcisk"] != odcisk:
            # pierwszy raz albo plik się zmienił — zaczynamy liczyć stabilność od nowa
            obserwowane[klucz] = {"odcisk": odcisk, "od": teraz}
            continue
        if teraz - wpis["od"] < a.stabilne:
            continue

        cel = wolna_nazwa(p.name, st.st_size)
        if cel is None:
            loguj(f"pomijam {klucz} — taki plik jest już w inbox/")
            odebrane[klucz] = odcisk
            obserwowane.pop(klucz, None)
            continue

        if a.sucho:
            print(f"[sucho] {klucz} → {cel}")
            continue
        przenies(p, cel)
        odebrane[klucz] = odcisk
        obserwowane.pop(klucz, None)
        nowe += 1
        loguj(f"odebrano {klucz} → {cel.name} ({st.st_size / 1024 / 1024:.1f} MB)")

    # plik usunięty w źródle nie ma już czego pilnować, ale wpis w `odebrane` zostaje:
    # gdyby telefon przysłał go ponownie, nie chcemy drugiej kopii w inbox/
    for klucz in list(obserwowane):
        if klucz not in widziane:
            obserwowane.pop(klucz)

    if not a.sucho:
        zapisz_stan(stan)
    if nowe:
        loguj(f"gotowe: {nowe} nowych nagrań w {INBOX}")


if __name__ == "__main__":
    main()
