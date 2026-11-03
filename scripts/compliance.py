#!/usr/bin/env python3
"""A6 — kontrola zgodności scenariusza i pakietu publikacji z granicami kanału (`CLAUDE.md`, strategia §7).

Wyłapuje to, co da się sprawdzić tekstowo. **Nie zastępuje bramki właściciela:** nie oceni, czy opis zdradza
logikę strategii, a liczby tylko wskazuje do sprawdzenia z kartą lub Ledgerem.

Kod wyjścia 1 przy błędach, 0 gdy zostają same uwagi.

    python3 scripts/compliance.py --script content/scripts/<slug>.md [--pakiet katalog_z_pakietem]
"""

from __future__ import annotations

import argparse
import re
import sys
from datetime import date
from pathlib import Path

WIERSZ = re.compile(r"^\|\s*(L\d{3,})\s*\|([^|]*)\|([^|]*)\|([^|]*)\|", re.MULTILINE)
ROZDZIAL = re.compile(r"^##\s*\[[^\]]+\]", re.MULTILINE)
DISCLAIMER = "Past performance does not guarantee future results"

ZAKAZANE_W_TYTULE = re.compile(r"\b(only|secret|AI|AI-powered|holy grail|guaranteed)\b|100\s?%", re.I)
KWOTA = re.compile(r"[$€£]\s?\d|\b\d[\d,.]*\s?(usd|eur|pln|dollars?)\b", re.I)
SPRZEDAZ_O_SOBIE = re.compile(r"\b(we|i)\s+(sell|offer)\b|\bour\s+(product|ea|offer|strategy for sale)\b"
                              r"|\bget\s+my\s+ea\b|\blink\s+to\s+purchase\b|\bbuy\s+(my|our)\b", re.I)
SPRZEDAZ_DO_OCENY = re.compile(r"\b(buy|discount|offer|purchase)\b", re.I)    # o innych wolno, trzeba przeczytać
TEMATY_ZAKAZANE = re.compile(r"\b(clients?|customers?|freelance|prompts?|JSON)\b", re.I)
SLOW_NA_MINUTE = 145
CTA_NAJWCZESNIEJ_S = 30
MAX_SLOW = 15


def front_matter(tekst: str) -> dict[str, str]:
    blok = re.match(r"---\n(.*?)\n---", tekst, re.S)
    if not blok:
        return {}
    pary = (l.split(":", 1) for l in blok[1].splitlines() if ":" in l)
    return {k.strip(): v.strip() for k, v in pary}


def sprawdz_tytul(tytul: str, bledy: list[str]) -> None:
    trafienie = ZAKAZANE_W_TYTULE.search(tytul)
    if trafienie:
        bledy.append(f"tytuł „{tytul}”: zakazane „{trafienie[0]}”")
    if KWOTA.search(tytul):
        bledy.append(f"tytuł „{tytul}”: kwota zysku")


def sprawdz_scenariusz(sciezka: Path, bledy: list[str], uwagi: list[str]) -> None:
    tekst = sciezka.read_text(encoding="utf-8")
    fm = front_matter(tekst)
    wiersze = [(m[1], m[2].strip(), m[3].strip(), m[4].strip()) for m in WIERSZ.finditer(tekst)]
    wiersze = [w for w in wiersze if w[1]]
    if not wiersze:
        bledy.append("brak wierszy z ID (L001…)")
        return

    if fm.get("tytul_roboczy"):
        sprawdz_tytul(fm["tytul_roboczy"], bledy)
    else:
        uwagi.append("brak tytul_roboczy w nagłówku")
    data = re.fullmatch(r"\d{4}-\d{2}-\d{2}", fm.get("publish_after", ""))
    if data and date.fromisoformat(data[0]) > date.today():
        bledy.append(f"embargo: publish_after {data[0]}")

    id_list = [w[0] for w in wiersze]
    if len(set(id_list)) != len(id_list):
        bledy.append("powtórzone ID zdań")
    if len(ROZDZIAL.findall(tekst)) < 3:
        bledy.append("mniej niż trzy sekcje, czyli za mało rozdziałów")
    if not any(DISCLAIMER.lower() in w[1].lower() for w in wiersze):
        bledy.append("brak zastrzeżenia: „Historical results, not investment advice…”")

    slow_razem, pierwsze_cta, zdanie_cta = 0, None, None
    liczby, do_oceny = [], []
    for id_, en, pl, ekran in wiersze:
        slowa = en.split()
        if len(slowa) > MAX_SLOW and DISCLAIMER.lower() not in en.lower():
            uwagi.append(f"{id_}: {len(slowa)} słów, limit to {MAX_SLOW}")
        if not pl:
            bledy.append(f"{id_}: brak tłumaczenia PL")
        trafienie = SPRZEDAZ_O_SOBIE.search(en)
        if trafienie:
            bledy.append(f"{id_}: język sprzedaży o sobie: „{trafienie[0]}”")
        elif SPRZEDAZ_DO_OCENY.search(en):
            do_oceny.append(id_)
        temat = TEMATY_ZAKAZANE.search(en)
        if temat:
            uwagi.append(f"{id_}: „{temat[0]}”: bez klientów, zleceń i promptów")
        if re.search(r"\d", en):
            liczby.append(id_)
        if pierwsze_cta is None and re.search(r"\b(subscribe|like)\b", en, re.I):
            pierwsze_cta, zdanie_cta = slow_razem / SLOW_NA_MINUTE * 60, id_
        slow_razem += len(slowa)

    if liczby:
        uwagi.append("liczby do sprawdzenia z Ledgerem lub kartą: " + ", ".join(liczby))
    if do_oceny:
        uwagi.append("słowa sprzedażowe do przeczytania (o innych wolno): " + ", ".join(do_oceny))
    if pierwsze_cta is None:
        uwagi.append("brak CTA głosem (standard §9)")
    elif pierwsze_cta < CTA_NAJWCZESNIEJ_S:
        bledy.append(f"{zdanie_cta}: CTA około {pierwsze_cta:.0f} s, najwcześniej po {CTA_NAJWCZESNIEJ_S} s")

    belki = [w for w in wiersze if w[3].upper().startswith("BELKA")]
    if len(belki) > 1:
        bledy.append("belka subskrypcji więcej niż raz: " + ", ".join(w[0] for w in belki))
    elif not belki:
        uwagi.append("brak `BELKA: subscribe` przy CTA")
    elif not re.search(r"\bsubscribe\b", belki[0][1], re.I):
        uwagi.append(f"{belki[0][0]}: belka przy zdaniu bez słowa „subscribe”")


def sprawdz_pakiet(katalog: Path, bledy: list[str], uwagi: list[str]) -> None:
    pliki = sorted(p for p in katalog.rglob("*") if p.suffix in (".md", ".txt"))
    if not pliki:
        uwagi.append(f"pakiet {katalog}: brak plików .md ani .txt")
    for plik in pliki:
        tekst = plik.read_text(encoding="utf-8")
        trafienie = SPRZEDAZ_O_SOBIE.search(tekst)
        if trafienie:
            bledy.append(f"{plik.name}: język sprzedaży o sobie: „{trafienie[0]}”")
        elif SPRZEDAZ_DO_OCENY.search(tekst):
            uwagi.append(f"{plik.name}: słowa sprzedażowe do przeczytania")
        if plik.stem.lower().startswith(("title", "tytul", "tytuly")):
            for linia in tekst.splitlines():
                linia = re.sub(r"^[\s#>*\-\d.)]+", "", linia).strip()
                if linia:
                    sprawdz_tytul(linia, bledy)


def main() -> None:
    ap = argparse.ArgumentParser(description="A6 — kontrola zgodności")
    ap.add_argument("--script", required=True, type=Path, help="content/scripts/<slug>.md")
    ap.add_argument("--pakiet", type=Path, help="katalog z pakietem publikacji")
    a = ap.parse_args()
    if not a.script.is_file():
        sys.exit(f"błąd: nie ma pliku {a.script}")

    bledy: list[str] = []
    uwagi: list[str] = []
    sprawdz_scenariusz(a.script, bledy, uwagi)
    if a.pakiet:
        sprawdz_pakiet(a.pakiet, bledy, uwagi)

    print(f"A6 {'FAIL' if bledy else ('UWAGI' if uwagi else 'OK')}: {a.script.name}")
    for b in bledy:
        print(f"     BŁĄD: {b}")
    for u in uwagi:
        print(f"     uwaga: {u}")
    if bledy:
        sys.exit(1)


if __name__ == "__main__":
    main()
