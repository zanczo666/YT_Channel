#!/usr/bin/env python3
"""C3 — dopasowanie transkrypcji do ID zdań scenariusza; wybór ostatniego czystego ujęcia.

Scenariusz (`content/scripts/<slug>.md`) ma każde zdanie w osobnym wierszu tabeli z ID (`L001`, `L002`…).
Ten skrypt odnajduje te zdania w transkrypcji nagrania i decyduje, który fragment taśmy zostaje:

1. dla każdego zdania szuka wszystkich ujęć w nagraniu (zdanie powtórzone = kilku kandydatów),
2. wybiera **jeden** ujęcie na zdanie tak, żeby kolejność zdań była zachowana (programowanie dynamiczne),
   a przy równej jakości wygrywa **ujęcie późniejsze** — czyli to, po którym już nie poprawiałeś,
3. wszystko poza wybranymi ujęciami (pauzy, pomyłki, odrzucone ujęcia) trafia na listę do wycięcia,
4. ujęcie, w którym Whisper schował urwany początek, przycina do ostatniego fragmentu mowy (patrz niżej).

Wynik: `align.json` (odcinki do zachowania i do wycięcia) + `align-raport.md` (czytelny raport „co wycięto”).

    python3 scripts/align.py --work /tmp/film-01 --script content/scripts/<slug>.md
"""

from __future__ import annotations

import argparse
import json
import re
import statistics
import subprocess
import sys
from difflib import SequenceMatcher
from pathlib import Path

WIERSZ_ID = re.compile(r"^\|\s*(L\d{3,})\s*\|([^|]*)\|", re.MULTILINE)
NAGLOWEK = re.compile(r"^##\s*\[([^\]]+)\]\s*(.+?)\s*$", re.MULTILINE)
TOKEN = re.compile(r"[a-z0-9']+")

PROG_DOPASOWANIA = 0.55     # poniżej tej zgodności uznajemy, że to nie jest to zdanie
WAGA_PEWNOSCI = 0.05        # lekka premia za czystsze ujęcie (średnia pewność słów)
# Oddech dosklejany do ujęcia. Asymetrycznie: na końcu zdania zostawiamy więcej, bo tam pada wydech
# i opadająca intonacja — ucięte zaraz po ostatniej głosce brzmi jak zatrzaśnięte drzwi.
# Pierwsza wersja (0,12 s z obu stron) dawała montaż, który właściciel ocenił jako „sztywny” (2026-11-02).
MARGINES_PRZED = 0.25
MARGINES_PO = 0.40
# Whisper potrafi pominąć urwany początek i „sorry”, a brakujący czas rozciągnąć na słowa poprawnego zdania
# (2026-11-03: L005, „until” trwało 4,2 s). Tekst wygląda wtedy czysto, więc pomyłkę widać dopiero
# w czasach słów i w dźwięku. Samo długie słowo to za mało: tak samo wygląda pauza w środku czytanego zdania.
DLUGIE_SLOWO = 1.0          # słowo od tej długości (s) każe zajrzeć do dźwięku
MIN_PRZERWA = 0.7           # krótsza cisza to oddech w zdaniu, nie granica ujęcia
CISZA_DB = -45
ZDANIE_W_BLOKU = 0.75       # ostatni fragment musi mieścić tyle całego zdania przy tempie mówcy…
SLOWA_W_BLOKU = 0.6         # …a słowa z transkrypcji mają zajmować mniej niż tyle jego czasu
# Whisper kończy słowo za wcześnie, zwłaszcza przy cichnącym głosie (2026-11-03: „results” z L012 straciło
# ~0,4 s i film urywał się w pełnym głosie), więc koniec zdania bierzemy z dźwięku.
OKNO_KONCA = 1.5            # jak daleko za końcem ze słów szukamy ciszy (s)
CISZA_KONCA = 0.15          # krótsze przerwy to jeszcze środek słowa


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
            sm = SequenceMatcher(None, cel, okno, autojunk=False)
            # Okno jest zgrubne (ułamki długości zdania), więc na końcach bywają słowa z sąsiedniego
            # zdania. Przycinamy do pierwszego i ostatniego słowa, które naprawdę pasuje — inaczej
            # ujęcie „zachodzi” na następne i programowanie dynamiczne musi jedno z nich odrzucić
            # (test 2026-11-02: tak wypadły L002 i L006, mimo że oba były w nagraniu).
            bloki = [b for b in sm.get_matching_blocks() if b.size]
            if not bloki:
                continue
            od_w, do_w = bloki[0].b, bloki[-1].b + bloki[-1].size - 1
            okno = okno[od_w:do_w + 1]
            wynik = SequenceMatcher(None, cel, okno, autojunk=False).ratio()
            if najlepszy is None or wynik > najlepszy["wynik"]:
                najlepszy = {"wynik": wynik, "od": i + od_w, "do": i + do_w}
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


def cisze_w_ujeciu(audio: Path, start: float, koniec: float,
                   min_cisza: float = MIN_PRZERWA) -> list[tuple[float, float | None]]:
    """Cisze w odcinku nagrania, w czasie całego pliku. Cisza trwająca do końca odcinka ma koniec None."""
    res = subprocess.run(["ffmpeg", "-nostdin", "-hide_banner", "-ss", f"{start:.3f}", "-t", f"{koniec - start:.3f}",
                          "-i", str(audio), "-af", f"silencedetect=noise={CISZA_DB}dB:d={min_cisza}",
                          "-f", "null", "-"], capture_output=True, text=True)
    pocz = [float(x) + start for x in re.findall(r"silence_start: ([\d.]+)", res.stderr)]
    konc = [float(x) + start for x in re.findall(r"silence_end: ([\d.]+)", res.stderr)]
    return [(p, konc[i] if i < len(konc) else None) for i, p in enumerate(pocz)]


def koniec_z_dzwieku(audio: Path, koniec: float) -> tuple[float, float | None]:
    """Prawdziwy koniec mowy i początek następnej. Bez ciszy w oknie zostaje koniec ze słów."""
    cisze = cisze_w_ujeciu(audio, koniec, koniec + OKNO_KONCA, CISZA_KONCA)
    if not cisze:
        return koniec, None
    return round(max(koniec, cisze[0][0]), 3), cisze[0][1]


def start_ostatniego_ujecia(kand: dict, slowa: list[dict], ile_tokenow: int, tempo: float,
                            audio: Path) -> float | None:
    """Nowy początek, jeśli w ujęciu schowało się urwane podejście; inaczej None.

    Przerwa z czytania ma po sobie tyle słów, ile mieści się w tym czasie. Po schowanej pomyłce ostatni
    fragment mowy jest długi jak całe zdanie, ale według transkrypcji padło w nim tylko kilka słów.
    """
    w_ujeciu = slowa[kand["od"]:kand["do"] + 1]
    if not any(w["koniec"] - w["start"] >= DLUGIE_SLOWO for w in w_ujeciu):
        return None
    for _, koniec_ciszy in reversed(cisze_w_ujeciu(audio, kand["start"], kand["koniec"])):
        if koniec_ciszy is None:
            continue
        blok = kand["koniec"] - koniec_ciszy
        slow_w_bloku = sum(1 for w in w_ujeciu if w["start"] >= koniec_ciszy)
        if blok >= ZDANIE_W_BLOKU * ile_tokenow * tempo and slow_w_bloku * tempo < SLOWA_W_BLOKU * blok:
            return round(koniec_ciszy, 3)
    return None


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
    ap.add_argument("--margines-przed", type=float, default=MARGINES_PRZED, help="oddech przed zdaniem (s)")
    ap.add_argument("--margines-po", type=float, default=MARGINES_PO, help="oddech po zdaniu (s)")
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

    audio = a.work / "audio.wav"
    tempo = statistics.median(w["koniec"] - w["start"] for w in slowa)
    przyciete, do_sprawdzenia = [], []
    for z, k in zip(zdania, wybor):
        if not k or not audio.is_file():
            continue
        k["koniec"], k["nastepna_mowa"] = koniec_z_dzwieku(audio, k["koniec"])
        nowy_start = start_ostatniego_ujecia(k, slowa, len(z["tokeny"]), tempo, audio)
        if nowy_start:
            przyciete.append({"start": round(k["start"], 3), "koniec": nowy_start,
                              "tekst": f"urwane podejście {z['id']}, którego transkrypcja nie zapisała",
                              "powod": "pomyłka schowana w ujęciu"})
            k["start"] = nowy_start
        elif any(w["koniec"] - w["start"] >= DLUGIE_SLOWO for w in slowa[k["od"]:k["do"] + 1]):
            do_sprawdzenia.append(z["id"])

    # Odcinki do zachowania. Oddech bierzemy z ciszy wokół ujęcia, ale nigdy nie wchodzimy w sąsiednie
    # ujęcie ani za jego połowę drogi — dzięki temu tam, gdzie nagrywałeś zdanie po zdaniu, w montażu
    # zostaje prawdziwa pauza z pokoju, a nie cisza doklejona z innego miejsca taśmy.
    uzyte = [(z, k) for z, k in zip(zdania, wybor) if k]
    zachowaj, pozycje = [], []
    for i, (z, kand) in enumerate(uzyte):
        poprzedni_koniec = uzyte[i - 1][1]["koniec"] if i else 0.0
        # bez kolejnego ujęcia ogranicza nas tylko margines; dalej może paść mowa spoza scenariusza
        nastepny_start = uzyte[i + 1][1]["start"] if i + 1 < len(uzyte) else kand["koniec"] + 2 * a.margines_po
        if kand.get("nastepna_mowa"):
            nastepny_start = min(nastepny_start, kand["nastepna_mowa"])
        start = max(poprzedni_koniec + (kand["start"] - poprzedni_koniec) / 2 if i else 0.0,
                    kand["start"] - a.margines_przed, 0.0)
        koniec = min(kand["koniec"] + (nastepny_start - kand["koniec"]) / 2,
                     kand["koniec"] + a.margines_po)
        if koniec <= start:                       # ujęcia stykają się — tniemy dokładnie na słowie
            start, koniec = kand["start"], kand["koniec"]
        zachowaj.append({"id": z["id"], "start": round(start, 3), "koniec": round(koniec, 3)})
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
    wyciete = sorted(wyciete + przyciete, key=lambda w: w["start"])

    dopasowane = sum(1 for k in wybor if k)
    wynik = {
        "scenariusz": str(a.script),
        "zdan": len(zdania),
        "dopasowanych": dopasowane,
        "czas_zachowany_s": round(sum(z["koniec"] - z["start"] for z in zachowaj), 2),
        "zachowaj": zachowaj,
        "wyciete": wyciete,
        "do_sprawdzenia": do_sprawdzenia,
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
            # rozróżniamy „nie ma czego montować” od „ujęcie jest, ale kłóci się z sąsiednim”
            powod = "**BRAK**" if not z["ujec_znalezionych"] else "**KONFLIKT**"
            linie.append(f"| {z['id']} | {z['rozdzial']} | {z['ujec_znalezionych']} | "
                         f"{powod} | — | — | {z['en'][:60]} |")
    linie += ["", "## Co zostało wycięte", ""]
    linie += [f"- `{w['start']:.1f}–{w['koniec']:.1f} s` ({w['powod']}): „{w['tekst'][:120]}”"
              for w in wyciete] or ["- nic"]
    if do_sprawdzenia:
        linie += ["", "## Do odsłuchu", "",
                  "W tych zdaniach jest długie słowo, ale wygląda to na pauzę, więc zostały całe: "
                  + ", ".join(do_sprawdzenia)]
    braki = [z for z in wynik["zdania"] if not z["wybrane_ujecie"] and not z["ujec_znalezionych"]]
    if braki:
        linie += ["", "## Zdania bez ujęcia (do dogrania)", ""]
        linie += [f"- **{z['id']}** ({z['rozdzial']}): {z['en']}" for z in braki]
    konflikty = [z for z in wynik["zdania"] if not z["wybrane_ujecie"] and z["ujec_znalezionych"]]
    if konflikty:
        linie += ["", "## Zdania z ujęciem, którego nie dało się użyć", "",
                  "Ujęcie jest w nagraniu, ale nachodzi na ujęcie sąsiedniego zdania — "
                  "zwykle znaczy to, że dwa zdania padły bez pauzy między nimi.", ""]
        linie += [f"- **{z['id']}** ({z['rozdzial']}): {z['en']}" for z in konflikty]
    (a.work / "align-raport.md").write_text("\n".join(linie) + "\n", encoding="utf-8")

    print(f"OK: {dopasowane}/{len(zdania)} zdań, {wynik['czas_zachowany_s']:.1f} s do zachowania, "
          f"{len(wyciete)} fragmentów do wycięcia")
    print(f"     {a.work / 'align.json'} + {a.work / 'align-raport.md'}")


if __name__ == "__main__":
    main()
