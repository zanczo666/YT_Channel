#!/usr/bin/env python3
"""Siatka podglądu wariantów miniatur (2×2 lub 2×3) do szybkiego wyboru i testu A/B w YouTube Studio.

Każdy wariant w dwóch rozmiarach: duży (640×360) i obok mały (168×94, jak na liście w telefonie).
Wymaga Pillow (uruchamiać `python3`, nie `python3 -I`).

Użycie:
    python3 scripts/thumbnail_grid.py --out content/publish/<slug>/grid.png content/publish/<slug>/thumbnail-*.jpg
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

BIG, SMALL = (640, 360), (168, 94)
FONT = "/usr/share/fonts/opentype/urw-base35/NimbusSans-Bold.otf"


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", required=True, type=Path)
    ap.add_argument("images", nargs="+", type=Path)
    a = ap.parse_args()

    cols = 2
    rows = (len(a.images) + cols - 1) // cols
    cell_w, cell_h = BIG[0] + SMALL[0] + 30, BIG[1] + 40
    sheet = Image.new("RGB", (cols * cell_w, rows * cell_h), (240, 240, 240))
    d = ImageDraw.Draw(sheet)
    font = ImageFont.truetype(FONT, 22)
    for i, path in enumerate(a.images):
        x, y = (i % cols) * cell_w, (i // cols) * cell_h
        img = Image.open(path).convert("RGB")
        sheet.paste(img.resize(BIG, Image.LANCZOS), (x + 10, y + 34))
        sheet.paste(img.resize(SMALL, Image.LANCZOS), (x + BIG[0] + 20, y + 34))
        d.text((x + 10, y + 6), f"{chr(65 + i)}: {path.name}", font=font, fill=(20, 20, 20))
    a.out.parent.mkdir(parents=True, exist_ok=True)
    sheet.save(a.out)
    print(a.out)
    return 0


if __name__ == "__main__":
    sys.exit(main())
