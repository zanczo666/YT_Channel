#!/usr/bin/env python3
"""C8 — napisy EN i PL: tekst ze scenariusza, czasy z nagrania.

Napisów nie bierzemy z transkrypcji, tylko ze scenariusza: Whisper słyszy „10 minutes” tam, gdzie
w scenariuszu jest „ten minutes”, gubi przecinki i nie zna pisowni nazw własnych. Scenariusz jest
źródłem tekstu, nagranie — źródłem czasu. Słowa scenariusza przypinamy do usłyszanych słów
(`SequenceMatcher`), a tym, których Whisper nie rozpoznał, czas interpolujemy między sąsiadami.

Czasy są w osi **montażu**, nie nagrania: `cut.json` mówi, gdzie każde zdanie wylądowało po cięciu.

Linia PL nie ma własnych czasów — polskie zdanie dzielimy na tyle samo kawałków co angielskie
i dajemy im te same czasy. Tłumaczenie bywa dłuższe, więc podział idzie po długości tekstu.

    python3 scripts/subtitles.py --work /tmp/film-01 --script content/scripts/<slug>.md
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from difflib import SequenceMatcher
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from align import MARGINES_PO, MARGINES_PRZED, czytaj_scenariusz, tokenizuj  # noqa: E402 — ten sam parser scenariusza

ZNAKI_W_LINII = 42      # norma czytelności: dwie linie po ~42 znaki mieszczą się w kadrze
LINIE = 2
MIN_CZAS = 1.0          # krócej niż sekunda widz nie zdąży przeczytać
MAX_CZAS = 7.0
PRZERWA = 0.08          # szczelina między napisami, żeby zmiana była widoczna

WIERSZ_PL = re.compile(r"^\|\s*(L\d{3,})\s*\|[^|]*\|([^|]*)\|", re.MULTILINE)


POKRYCIE_SLOW = 0.7   # poniżej tej części zdania czasy słów z transkrypcji nie są wiarygodne


def czas_srt(s: float) -> str:
    s = max(0.0, s)
    g, reszta = divmod(int(s), 3600)
    m, sek = divmod(reszta, 60)
    return f"{g:02d}:{m:02d}:{sek:02d},{round((s - int(s)) * 1000):03d}"


def czasy_slow(zdanie: list[str], slowa: list[dict]) -> list[tuple[float, float]]:
    """Każdemu słowu scenariusza przypisz czas usłyszanego słowa; brakującym — interpolowany."""
    uslyszane = [tokenizuj(w["slowo"])[0] if tokenizuj(w["slowo"]) else "" for w in slowa]
    czasy: list[tuple[float, float] | None] = [None] * len(zdanie)
    for blok in SequenceMatcher(None, zdanie, uslyszane, autojunk=False).get_matching_blocks():
        for k in range(blok.size):
            w = slowa[blok.b + k]
            czasy[blok.a + k] = (w["start"], w["koniec"])

    znane = [i for i, c in enumerate(czasy) if c]
    if not znane:                       # nic nie trafiło — rozkładamy zdanie równo na całym ujęciu
        od, do = slowa[0]["start"], slowa[-1]["koniec"]
        krok = (do - od) / len(zdanie)
        return [(od + i * krok, od + (i + 1) * krok) for i in range(len(zdanie))]

    for i in range(len(czasy)):         # brzegi i dziury: ciągniemy czas od najbliższego znanego słowa
        if czasy[i]:
            continue
        lewy = max((j for j in znane if j < i), default=None)
        prawy = min((j for j in znane if j > i), default=None)
        if lewy is None:
            czasy[i] = (czasy[prawy][0], czasy[prawy][0])
        elif prawy is None:
            czasy[i] = (czasy[lewy][1], czasy[lewy][1])
        else:
            od, do = czasy[lewy][1], czasy[prawy][0]
            ile = prawy - lewy
            k = i - lewy
            czasy[i] = (od + (do - od) * (k - 1) / ile, od + (do - od) * k / ile)
    return czasy  # type: ignore[return-value]


def podziel(slowa: list[str], ile_kawalkow: int | None = None) -> list[list[int]]:
    """Zdanie na kawałki mieszczące się w dwóch liniach; zwraca indeksy słów w każdym kawałku."""
    limit = ZNAKI_W_LINII * LINIE
    if ile_kawalkow:
        # podział wymuszony (wersja PL): po długości, żeby kawałki były porównywalne
        razem = sum(len(w) + 1 for w in slowa)
        cel = razem / ile_kawalkow
        kawalki, biezacy, dlugosc = [], [], 0.0
        for i, w in enumerate(slowa):
            biezacy.append(i)
            dlugosc += len(w) + 1
            # chętniej łamiemy po przecinku albo kropce — napis urwany w środku zdania podrzędnego
            # czyta się gorzej niż trochę krótszy, ale domknięty
            domkniete = w.endswith((".", ",", "!", "?", ":", ";", "—"))
            nastepne_domyka = i + 1 < len(slowa) and slowa[i + 1].endswith((".", ",", "!", "?", ":", ";"))
            prog = cel * (0.75 if domkniete else 1.0)
            if dlugosc >= prog and not (nastepne_domyka and dlugosc + len(slowa[i + 1]) < cel * 1.25) \
                    and len(kawalki) < ile_kawalkow - 1:
                kawalki.append(biezacy); biezacy, dlugosc = [], 0.0
        if biezacy:
            kawalki.append(biezacy)
        while len(kawalki) < ile_kawalkow:        # bardzo krótkie zdanie — oddajemy puste kawałki
            kawalki.append([])
        return kawalki

    # Najpierw liczymy, na ile kawałków zdanie MUSI się rozpaść, a potem dzielimy je równo.
    # Zachłanne napełnianie do limitu zostawiało na końcu sierotę w rodzaju „przyszłych.” na sekundę.
    razem = sum(len(w) + 1 for w in slowa) - 1
    ile = max(1, -(-razem // limit))
    return podziel(slowa, ile) if ile > 1 else [list(range(len(slowa)))]


def zlam(tekst: str) -> str:
    """Dwie linie zamiast jednej długiej — łamiemy blisko środka, na granicy słowa."""
    if len(tekst) <= ZNAKI_W_LINII:
        return tekst
    slowa = tekst.split()
    srodek, najlepszy, ocena = len(tekst) / 2, 1, None
    for i in range(1, len(slowa)):
        gora, dol = " ".join(slowa[:i]), " ".join(slowa[i:])
        # kara za przekroczenie szerokości kadru jest większa niż za nierówny podział
        kara = abs(len(gora) - srodek) + 100 * (max(0, len(gora) - ZNAKI_W_LINII)
                                                + max(0, len(dol) - ZNAKI_W_LINII))
        if ocena is None or kara < ocena:
            ocena, najlepszy = kara, i
    return " ".join(slowa[:najlepszy]) + "\n" + " ".join(slowa[najlepszy:])


def zapisz_srt(wpisy: list[dict], path: Path) -> None:
    bloki = [f"{i}\n{czas_srt(w['od'])} --> {czas_srt(w['do'])}\n{zlam(w['tekst'])}\n"
             for i, w in enumerate(wpisy, 1)]
    path.write_text("\n".join(bloki), encoding="utf-8")


def main() -> None:
    ap = argparse.ArgumentParser(description="C8 — napisy EN i PL")
    ap.add_argument("--work", required=True, type=Path, help="katalog roboczy (z cut.json)")
    ap.add_argument("--script", required=True, type=Path, help="content/scripts/<slug>.md")
    a = ap.parse_args()

    for plik in ("cut.json", "transcript.json"):
        if not (a.work / plik).is_file():
            sys.exit(f"błąd: brak {a.work / plik} — najpierw uruchom cut.py")

    cut = json.loads((a.work / "cut.json").read_text(encoding="utf-8"))
    slowa = json.loads((a.work / "transcript.json").read_text(encoding="utf-8"))["slowa"]
    zdania = {z["id"]: z for z in czytaj_scenariusz(a.script)}
    pl = {m.group(1): m.group(2).strip() for m in WIERSZ_PL.finditer(a.script.read_text(encoding="utf-8"))}

    wpisy_en: list[dict] = []
    wpisy_pl: list[dict] = []
    for odcinek in cut["os_czasu"]:
        zdanie = zdania.get(odcinek["id"])
        if not zdanie:
            continue
        przesuniecie = odcinek["montaz_start"] - odcinek["zrodlo_start"]
        w_odcinku = [w for w in slowa
                     if w["start"] >= odcinek["zrodlo_start"] - 0.01
                     and w["koniec"] <= odcinek["zrodlo_koniec"] + 0.01]
        slowa_en = zdanie["en"].split()
        if not w_odcinku:
            continue
        czasy = czasy_slow(tokenizuj(zdanie["en"]), w_odcinku)
        # tokenizuj() gubi interpunkcję, więc może dać mniej elementów niż jest słów do wyświetlenia
        # Po przycięciu schowanej pomyłki (C3) część słów ma czasy sprzed początku odcinka i wypada z listy.
        # Pozostałe nie opisują całego zdania, więc czas rozkładamy równo na mowę w odcinku.
        niepelne = len(w_odcinku) < POKRYCIE_SLOW * len(slowa_en)
        if niepelne or len(czasy) != len(slowa_en):
            od, do = w_odcinku[0]["start"], w_odcinku[-1]["koniec"]
            if niepelne:
                od, do = odcinek["zrodlo_start"] + MARGINES_PRZED, odcinek["zrodlo_koniec"] - MARGINES_PO
            krok = (do - od) / max(1, len(slowa_en))
            czasy = [(od + i * krok, od + (i + 1) * krok) for i in range(len(slowa_en))]

        kawalki = podziel(slowa_en)
        for k in kawalki:
            od = czasy[k[0]][0] + przesuniecie
            do = max(czasy[k[-1]][1] + przesuniecie, od + MIN_CZAS)
            wpisy_en.append({"od": od, "do": min(do, od + MAX_CZAS),
                             "tekst": " ".join(slowa_en[i] for i in k), "id": odcinek["id"]})

        # PL dzielimy po swojemu: tłumaczenie bywa dłuższe od oryginału i wymuszanie tej samej liczby
        # kawałków co w EN dawało linie nie do przeczytania. Czasy rozkładamy proporcjonalnie
        # do długości tekstu w obrębie zdania — tłumaczenie i tak nie ma własnych granic słów w nagraniu.
        tekst_pl = pl.get(odcinek["id"], "")
        if tekst_pl:
            slowa_pl = tekst_pl.split()
            kawalki_pl = podziel(slowa_pl)
            poczatek = czasy[0][0] + przesuniecie
            koniec_zd = czasy[-1][1] + przesuniecie
            razem = sum(len(w) + 1 for w in slowa_pl)
            uplyw = 0.0
            for k in kawalki_pl:
                dlugosc_k = sum(len(slowa_pl[i]) + 1 for i in k)
                od = poczatek + (koniec_zd - poczatek) * uplyw / razem
                uplyw += dlugosc_k
                do = poczatek + (koniec_zd - poczatek) * uplyw / razem
                wpisy_pl.append({"od": od, "do": max(do, od + MIN_CZAS),
                                 "tekst": " ".join(slowa_pl[i] for i in k), "id": odcinek["id"]})

    # napisy nie mogą na siebie nachodzić — kolejny zaczyna się po poprzednim
    for wpisy in (wpisy_en, wpisy_pl):
        for i in range(len(wpisy) - 1):
            if wpisy[i]["do"] > wpisy[i + 1]["od"] - PRZERWA:
                wpisy[i]["do"] = max(wpisy[i]["od"] + 0.3, wpisy[i + 1]["od"] - PRZERWA)

    zapisz_srt(wpisy_en, a.work / "napisy-en.srt")
    zapisz_srt(wpisy_pl, a.work / "napisy-pl.srt")
    dlugie = [w for w in wpisy_en + wpisy_pl if len(w["tekst"]) > ZNAKI_W_LINII * LINIE]
    print(f"OK: {len(wpisy_en)} napisów EN, {len(wpisy_pl)} PL"
          + (f"; {len(dlugie)} za długich do sprawdzenia" if dlugie else ""))
    print(f"     {a.work / 'napisy-en.srt'} + {a.work / 'napisy-pl.srt'}")


if __name__ == "__main__":
    main()
