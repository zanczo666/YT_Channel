#!/usr/bin/env python3
"""C3 — dopasowanie transkrypcji do ID zdań scenariusza; wybór ostatniego czystego ujęcia.

Scenariusz (`content/scripts/<slug>.md`) ma każde zdanie w osobnym wierszu tabeli z ID (`L001`, `L002`…).
Ten skrypt odnajduje te zdania w transkrypcji nagrania i decyduje, który fragment taśmy zostaje:

1. dla każdego zdania szuka wszystkich ujęć w nagraniu (zdanie powtórzone = kilku kandydatów),
2. wybiera **jeden** ujęcie na zdanie tak, żeby kolejność zdań była zachowana (programowanie dynamiczne),
   a przy równej jakości wygrywa **ujęcie późniejsze** — czyli to, po którym już nie poprawiałeś,
3. wszystko poza wybranymi ujęciami (pauzy, pomyłki, odrzucone ujęcia) trafia na listę do wycięcia.

Wynik: `align.json` (odcinki do zachowania i do wycięcia) + `align-raport.md` (czytelny raport „co wycięto”).

    python3 scripts/align.py --work /tmp/film-01 --script content/scripts/<slug>.md
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from difflib import SequenceMatcher
from pathlib import Path

WIERSZ_ID = re.compile(r"^\|\s*(L\d{3,})\s*\|([^|]*)\|", re.MULTILINE)
NAGLOWEK = re.compile(r"^##\s*\[([^\]]+)\]\s*(.+?)\s*$", re.MULTILINE)
TOKEN = re.compile(r"[a-z0-9']+")

PROG_DOPASOWANIA = 0.55     # poniżej tej zgodności uznajemy, że to nie jest to zdanie
WAGA_PEWNOSCI = 0.05        # lekka premia za czystsze ujęcie (średnia pewność słów)
MARGINES_S = 0.12           # oddech dosklejany do każdego ujęcia przy cięciu


def tokenizuj(tekst: str) -> list[str]:
    return TOKEN.findall(tekst.lower())


def czytaj_scenariusz(path: Path) -> list[dict]:
    """Zdania z tabel scenariusza, w kolejności występowania, z rozdziałem, do którego należą."""
    tekst = path.read_text(encoding="utf-8")
    rozdzialy = [(m.start(), m.group(2)) for m in NAGLOWEK.finditer(tekst)]
    zdania = []
    for m in WIERSZ_ID.finditer(tekst):
        en = m.group(2).strip()
        if not en:
            continue                      # pusty wiersz szablonu
        rozdzial = next((n for p, n in reversed(rozdzialy) if p < m.start()), "—")
        zdania.append({"id": m.group(1), "en": en, "rozdzial": rozdzial, "tokeny": tokenizuj(en)})
    return [z for z in zdania if z["tokeny"]]


def kandydaci(zdanie: dict, slowa: list[dict], tokeny: list[str]) -> list[dict]:
    """Wszystkie miejsca w nagraniu, w których zdanie zostało (choćby niedokładnie) wypowiedziane."""
    cel = zdanie["tokeny"]
    n = len(cel)
    dlugosci = sorted({max(1, int(n * f)) for f in (0.6, 0.8, 1.0, 1.25, 1.5)})
    # kotwice: pozycje, w których padło pierwsze słowo zdania — bez tego skanowalibyśmy całe nagranie
    starty = [i for i, t in enumerate(tokeny) if t == cel[0]]
    if not starty:
        starty = range(len(tokeny))

    znalezione: list[dict] = []
    for i in starty:
        najlepszy = None
        for dl in dlugosci:
            okno = tokeny[i:i + dl]
            if not okno:
                continue
            wynik = SequenceMatcher(None, cel, okno, autojunk=False).ratio()
            if najlepszy is None or wynik > najlepszy["wynik"]:
                najlepszy = {"wynik": wynik, "od": i, "do": i + len(okno) - 1}
        if najlepszy and najlepszy["wynik"] >= PROG_DOPASOWANIA:
            znalezione.append(najlepszy)

    # z nakładających się kotwic zostawiamy najlepszą — inaczej jedno ujęcie liczyłoby się wielokrotnie
    znalezione.sort(key=lambda k: (-k["wynik"], k["od"]))
    wybrane: list[dict] = []
    for k in znalezione:
        if all(k["do"] < w["od"] or k["od"] > w["do"] for w in wybrane):
            pewnosci = [slowa[j]["pewnosc"] for j in range(k["od"], k["do"] + 1)]
            k["pewnosc"] = round(sum(pewnosci) / len(pewnosci), 3)
            k["start"] = slowa[k["od"]]["start"]
            k["koniec"] = slowa[k["do"]]["koniec"]
            k["tekst"] = " ".join(slowa[j]["slowo"] for j in range(k["od"], k["do"] + 1))
            wybrane.append(k)
    wybrane.sort(key=lambda k: k["od"])
    return wybrane


def wybierz_ujecia(zdania: list[dict], wszyscy: list[list[dict]]) -> list[dict | None]:
    """Po jednym ujęciu na zdanie, z zachowaniem kolejności; przy remisie wygrywa ujęcie późniejsze.

    Programowanie dynamiczne po zdaniach: `najlepsze[i][k]` = najlepsza suma ocen dla zdań 0..i,
    gdy zdanie i bierzemy z ujęcia k. Zdanie wolno pominąć (ocena 0) — mówca mógł opuścić linijkę.
    """
    n = len(zdania)
    suma: list[list[float]] = []
    skad: list[list[tuple[int, int] | None]] = []

    for i in range(n):
        suma.append([]); skad.append([])
        for k, kand in enumerate(wszyscy[i]):
            ocena = kand["wynik"] + WAGA_PEWNOSCI * kand["pewnosc"]
            najlepsza, zrodlo = 0.0, None
            for p in range(i):                      # ostatnie zdanie przed i, które faktycznie weszło
                for q, poprz in enumerate(wszyscy[p]):
                    if poprz["do"] < kand["od"] and suma[p][q] >= najlepsza:
                        najlepsza, zrodlo = suma[p][q], (p, q)
            suma[i].append(najlepsza + ocena)
            skad[i].append(zrodlo)

    # koniec łańcucha: najwyższa suma, a przy remisie łańcuch kończący się później
    koniec, best = None, -1.0
    for i in range(n):
        for k in range(len(wszyscy[i])):
            if suma[i][k] > best or (suma[i][k] == best and koniec and wszyscy[i][k]["od"] >= wszyscy[koniec[0]][koniec[1]]["od"]):
                best, koniec = suma[i][k], (i, k)

    wybor: list[dict | None] = [None] * n
    while koniec:
        i, k = koniec
        wybor[i] = wszyscy[i][k]
        koniec = skad[i][k]
    return wybor


def main() -> None:
    ap = argparse.ArgumentParser(description="C3 — dopasowanie nagrania do ID zdań scenariusza")
    ap.add_argument("--work", required=True, type=Path, help="katalog roboczy (z transcript.json)")
    ap.add_argument("--script", required=True, type=Path, help="content/scripts/<slug>.md")
    ap.add_argument("--margines", type=float, default=MARGINES_S, help="oddech wokół ujęcia w sekundach")
    a = ap.parse_args()

    tr_path = a.work / "transcript.json"
    if not tr_path.is_file():
        sys.exit(f"błąd: brak {tr_path} — najpierw uruchom transcribe.py")
    transkrypcja = json.loads(tr_path.read_text(encoding="utf-8"))
    slowa = transkrypcja["slowa"]
    if not slowa:
        sys.exit("błąd: transkrypcja nie ma słów (puste nagranie albo sama cisza)")
    tokeny = [tokenizuj(w["slowo"])[0] if tokenizuj(w["slowo"]) else "" for w in slowa]

    zdania = czytaj_scenariusz(a.script)
    if not zdania:
        sys.exit(f"błąd: w {a.script} nie znalazłem wierszy z ID (L001…)")

    wszyscy = [kandydaci(z, slowa, tokeny) for z in zdania]
    wybor = wybierz_ujecia(zdania, wszyscy)

    # odcinki do zachowania
    zachowaj, pozycje = [], []
    for z, kand in zip(zdania, wybor):
        if not kand:
            continue
        zachowaj.append({"id": z["id"], "start": round(max(0.0, kand["start"] - a.margines), 3),
                         "koniec": round(kand["koniec"] + a.margines, 3)})
        pozycje.append((kand["od"], kand["do"]))

    # wszystko poza wybranymi ujęciami idzie do wycięcia; opisujemy, co tam było słychać
    wyciete, kursor = [], 0
    for (od, do), zach in zip(pozycje, zachowaj):
        if od > kursor:
            tekst = " ".join(slowa[j]["slowo"] for j in range(kursor, od))
            wyciete.append({"start": round(slowa[kursor]["start"], 3), "koniec": round(slowa[od - 1]["koniec"], 3),
                            "tekst": tekst, "powod": "odrzucone ujęcie lub pomyłka"})
        kursor = do + 1
    if kursor < len(slowa):
        wyciete.append({"start": round(slowa[kursor]["start"], 3), "koniec": round(slowa[-1]["koniec"], 3),
                        "tekst": " ".join(slowa[j]["slowo"] for j in range(kursor, len(slowa))),
                        "powod": "ogon nagrania"})

    dopasowane = sum(1 for k in wybor if k)
    wynik = {
        "scenariusz": str(a.script),
        "zdan": len(zdania),
        "dopasowanych": dopasowane,
        "czas_zachowany_s": round(sum(z["koniec"] - z["start"] for z in zachowaj), 2),
        "zachowaj": zachowaj,
        "wyciete": wyciete,
        "zdania": [{"id": z["id"], "rozdzial": z["rozdzial"], "en": z["en"],
                    "ujec_znalezionych": len(w),
                    "wybrane_ujecie": (w.index(k) + 1) if k else None,
                    "zgodnosc": round(k["wynik"], 3) if k else None,
                    "pewnosc": k["pewnosc"] if k else None,
                    "start": k["start"] if k else None, "koniec": k["koniec"] if k else None,
                    "uslyszane": k["tekst"] if k else None}
                   for z, w, k in zip(zdania, wszyscy, wybor)],
    }
    (a.work / "align.json").write_text(json.dumps(wynik, ensure_ascii=False, indent=2), encoding="utf-8")

    # raport dla człowieka
    linie = [f"# Dopasowanie nagrania do scenariusza — {a.script.name}", "",
             f"Zdania: **{dopasowane}/{len(zdania)}** dopasowane. "
             f"Materiał po cięciu: **{wynik['czas_zachowany_s']:.1f} s** "
             f"z {transkrypcja['czas_audio_s']:.1f} s nagrania.", "",
             "| ID | Rozdział | Ujęć | Wybrane | Zgodność | Start | Zdanie |", "|---|---|---|---|---|---|---|"]
    for z in wynik["zdania"]:
        if z["wybrane_ujecie"]:
            linie.append(f"| {z['id']} | {z['rozdzial']} | {z['ujec_znalezionych']} | "
                         f"{z['wybrane_ujecie']} | {z['zgodnosc']:.2f} | {z['start']:.1f} s | {z['en'][:60]} |")
        else:
            linie.append(f"| {z['id']} | {z['rozdzial']} | 0 | **BRAK** | — | — | {z['en'][:60]} |")
    linie += ["", "## Co zostało wycięte", ""]
    linie += [f"- `{w['start']:.1f}–{w['koniec']:.1f} s` ({w['powod']}): „{w['tekst'][:120]}”"
              for w in wyciete] or ["- nic"]
    braki = [z for z in wynik["zdania"] if not z["wybrane_ujecie"]]
    if braki:
        linie += ["", "## Zdania bez ujęcia (do dogrania)", ""]
        linie += [f"- **{z['id']}** ({z['rozdzial']}): {z['en']}" for z in braki]
    (a.work / "align-raport.md").write_text("\n".join(linie) + "\n", encoding="utf-8")

    print(f"OK: {dopasowane}/{len(zdania)} zdań, {wynik['czas_zachowany_s']:.1f} s do zachowania, "
          f"{len(wyciete)} fragmentów do wycięcia")
    print(f"     {a.work / 'align.json'} + {a.work / 'align-raport.md'}")


if __name__ == "__main__":
    main()
