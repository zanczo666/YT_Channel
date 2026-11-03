#!/usr/bin/env python3
"""F2 — szkice wyglądu kanału: awatar, baner i znak wodny w palecie miniatur i grafik.

    python3 scripts/brand.py --out assets/brand
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from PIL import Image, ImageDraw

sys.path.insert(0, str(Path(__file__).resolve().parent))
from graphics import AKCENTY, BG, FONT_BOLD, FONT_ZWYKLY, GRID, PRZYGASZONY, TEXT, font  # noqa: E402

IMIE_NAZWISKO = "RADOSLAW LUBAS"
OPIS = "SYSTEMATIC TRADING LAB"
HASLO = "I build and stress-test trading systems in public, and I publish what fails."
AKCENT = AKCENTY["pass"]
BANER = (2560, 1440)
STREFA_BANERA = (1546, 423)    # to jedyny obszar widoczny na każdym urządzeniu


def siatka(rysuj: ImageDraw.ImageDraw, szer: int, wys: int, krok: int) -> None:
    for x in range(0, szer, krok):
        rysuj.line([(x, 0), (x, wys)], fill=GRID, width=1)
    for y in range(0, wys, krok):
        rysuj.line([(0, y), (szer, y)], fill=GRID, width=1)


def awatar(cel: Path) -> None:
    obraz = Image.new("RGB", (800, 800), BG)
    rysuj = ImageDraw.Draw(obraz)
    rysuj.text((400, 385), "RL", font=font(FONT_BOLD, 430), fill=TEXT, anchor="mm")
    rysuj.rectangle([250, 590, 550, 612], fill=AKCENT)
    obraz.save(cel)


def baner(cel: Path) -> None:
    szer, wys = BANER
    obraz = Image.new("RGB", BANER, BG)
    rysuj = ImageDraw.Draw(obraz)
    siatka(rysuj, szer, wys, 80)
    gora = (wys - STREFA_BANERA[1]) // 2
    rysuj.text((szer // 2, gora + 105), IMIE_NAZWISKO, font=font(FONT_BOLD, 136), fill=TEXT, anchor="mm")
    rysuj.text((szer // 2, gora + 225), OPIS, font=font(FONT_BOLD, 68), fill=AKCENT, anchor="mm")
    rysuj.text((szer // 2, gora + 325), HASLO, font=font(FONT_ZWYKLY, 42), fill=PRZYGASZONY, anchor="mm")
    obraz.save(cel, quality=92)


def znak_wodny(cel: Path) -> None:
    obraz = Image.new("RGBA", (150, 150), (0, 0, 0, 0))
    rysuj = ImageDraw.Draw(obraz)
    rysuj.rounded_rectangle([4, 4, 146, 146], radius=26, fill=(*BG, 235))
    rysuj.text((75, 68), "RL", font=font(FONT_BOLD, 82), fill=TEXT, anchor="mm")
    rysuj.rectangle([44, 116, 106, 122], fill=AKCENT)
    obraz.save(cel)


def main() -> None:
    ap = argparse.ArgumentParser(description="F2 — awatar, baner, znak wodny")
    ap.add_argument("--out", type=Path, default=Path("assets/brand"))
    a = ap.parse_args()
    a.out.mkdir(parents=True, exist_ok=True)
    awatar(a.out / "awatar.png")
    baner(a.out / "baner.png")
    znak_wodny(a.out / "znak-wodny.png")
    print(f"OK: {a.out}/awatar.png, baner.png, znak-wodny.png")


if __name__ == "__main__":
    main()
