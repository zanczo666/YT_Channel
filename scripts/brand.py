#!/usr/bin/env python3
"""F2 — wygląd kanału: awatar, baner i znak wodny, odtworzone w kodzie z wersji wybranych przez właściciela.

Układ pochodzi ze szkiców z modelu graficznego (2026-11-05). Tu dostaje dokładne wymiary, poprawny tekst
i przezroczystość. Wszystko rysujemy w czterokrotnej rozdzielczości, bo Pillow nie wygładza krawędzi.

    python3 scripts/brand.py --out assets/brand
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

KATALOG = Path(__file__).resolve().parent
sys.path.insert(0, str(KATALOG))
from graphics import AKCENTY, BG, FONT_ZWYKLY, GRID, PRZYGASZONY, TEXT, font  # noqa: E402

FONT_MARKI = KATALOG.parent / "assets" / "fonts" / "Anton-Regular.ttf"
IMIE_NAZWISKO = "RADOSLAW LUBAS"
OPIS = "SYSTEMATIC TRADING LAB"
HASLO = "I build and stress-test trading systems in public, and I publish what fails."
AKCENT = AKCENTY["pass"]
BANER = (2560, 1440)
STREFA_BANERA = (1546, 423)    # jedyny obszar widoczny na każdym urządzeniu
SS = 4                         # nadpróbkowanie
PRZERWY_PIERSCIENIA = (45, 135, 225, 315)   # stopnie; przerwy po skosie zostawiają czytelny okrąg


def marka(rozmiar: int) -> ImageFont.FreeTypeFont:
    return ImageFont.truetype(str(FONT_MARKI), rozmiar)


def pierscien(rysuj: ImageDraw.ImageDraw, srodek: float, promien: float, grubosc: int,
              kolor: tuple[int, int, int], przerwa: float = 0.0) -> None:
    ramka = [srodek - promien, srodek - promien, srodek + promien, srodek + promien]
    if not przerwa:
        rysuj.ellipse(ramka, outline=kolor, width=grubosc)
        return
    for kat in PRZERWY_PIERSCIENIA:
        rysuj.arc(ramka, kat + przerwa / 2, kat + 90 - przerwa / 2, fill=kolor, width=grubosc)


def znak(rozmiar: int, tlo: bool = True) -> Image.Image:
    """RL w pierścieniu. Linie są grube: ten sam znak ma działać przy 800 px i przy 32 px."""
    r = rozmiar * SS
    obraz = Image.new("RGBA", (r, r), (*BG, 255) if tlo else (0, 0, 0, 0))
    rysuj = ImageDraw.Draw(obraz)
    s = r / 2
    if not tlo:     # znak wodny leży na filmie, więc sam niesie swoje tło
        rysuj.ellipse([r * 0.01, r * 0.01, r * 0.99, r * 0.99], fill=(*BG, 240))
    pierscien(rysuj, s, r * 0.415, max(1, round(r * 0.034)), AKCENT, przerwa=12)
    pierscien(rysuj, s, r * 0.355, max(1, round(r * 0.010)), TEXT)
    rysuj.text((s, s), "RL", font=marka(round(r * 0.36)), fill=TEXT, anchor="mm")
    return obraz.resize((rozmiar, rozmiar), Image.LANCZOS)


def diagram_etapow(rysuj: ImageDraw.ImageDraw, szer: int, y: int) -> None:
    """Etapy testu; jedna strategia odpada po drodze. Leży poniżej strefy, więc na telefonie po prostu znika."""
    ksztalty = "oosososs"
    krok, r, odrzucony = 200, 22, 4
    x0 = (szer - krok * (len(ksztalty) - 1)) // 2
    for i, k in enumerate(ksztalty):
        x = x0 + i * krok
        if k == "o":
            rysuj.ellipse([x - r, y - r, x + r, y + r], outline=TEXT, width=4)
        else:
            rysuj.rectangle([x - r, y - r, x + r, y + r], outline=TEXT, width=4)
        if i < len(ksztalty) - 1:
            xs, xk = x + r + 10, x + krok - r - 10
            rysuj.line([(xs, y), (xk, y)], fill=AKCENT, width=4)
            rysuj.polygon([(xk, y), (xk - 16, y - 10), (xk - 16, y + 10)], fill=AKCENT)
        if i == odrzucony:
            rysuj.line([(x, y + r + 6), (x, y + 72), (x + 62, y + 72)], fill=TEXT, width=4)
            xk = x + 90
            rysuj.line([(xk - 16, y + 56), (xk + 16, y + 88)], fill=TEXT, width=5)
            rysuj.line([(xk - 16, y + 88), (xk + 16, y + 56)], fill=TEXT, width=5)


def baner(cel: Path) -> None:
    szer, wys = BANER
    obraz = Image.new("RGB", BANER, BG)
    rysuj = ImageDraw.Draw(obraz)
    for y in range(0, wys, 80):
        rysuj.line([(0, y), (szer, y)], fill=GRID, width=2)
    gora = (wys - STREFA_BANERA[1]) // 2
    # pas pod tekstem, żeby linie tła nie przecinały liter
    rysuj.rectangle([(szer - STREFA_BANERA[0]) // 2, gora, (szer + STREFA_BANERA[0]) // 2, gora + STREFA_BANERA[1]],
                    fill=BG)
    rysuj.text((szer // 2, gora + 125), IMIE_NAZWISKO, font=marka(170), fill=TEXT, anchor="mm")
    rysuj.text((szer // 2, gora + 275), OPIS, font=font(FONT_ZWYKLY, 74), fill=PRZYGASZONY, anchor="mm")
    rysuj.text((szer // 2, gora + 365), HASLO, font=font(FONT_ZWYKLY, 44), fill=TEXT, anchor="mm")
    diagram_etapow(rysuj, szer, gora + STREFA_BANERA[1] + 60)
    obraz.save(cel)


def main() -> None:
    ap = argparse.ArgumentParser(description="F2 — awatar, baner, znak wodny")
    ap.add_argument("--out", type=Path, default=Path("assets/brand"))
    a = ap.parse_args()
    a.out.mkdir(parents=True, exist_ok=True)
    znak(800).convert("RGB").save(a.out / "awatar.png")
    baner(a.out / "baner.png")
    znak(150, tlo=False).save(a.out / "znak-wodny.png")
    print(f"OK: {a.out}/awatar.png, baner.png, znak-wodny.png")


if __name__ == "__main__":
    main()
