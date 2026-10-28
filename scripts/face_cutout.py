#!/usr/bin/env python3
"""Wycinanie tła ze zdjęć twarzy (lokalnie, rembg — zdjęcia nie opuszczają serwera).

Obraca wg EXIF, zmniejsza do max 1600 px wysokości, usuwa tło, przycina do sylwetki i zapisuje PNG
z przezroczystością. Uruchamiać interpreterem z venv, w którym jest rembg:

    /home/claude/.venvs/rembg/bin/python scripts/face_cutout.py --out assets/face/cut assets/face/raw/*.jpg
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from PIL import Image, ImageOps
from rembg import new_session, remove

MAX_H = 1600


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", required=True, type=Path)
    ap.add_argument("--model", default="u2net_human_seg", help="np. u2net_human_seg, birefnet-portrait")
    ap.add_argument("images", nargs="+", type=Path)
    a = ap.parse_args()

    a.out.mkdir(parents=True, exist_ok=True)
    session = new_session(a.model)
    for path in a.images:
        img = ImageOps.exif_transpose(Image.open(path)).convert("RGB")
        if img.height > MAX_H:
            img.thumbnail((MAX_H * 2, MAX_H))
        cut = remove(img, session=session, post_process_mask=True)
        bbox = cut.getchannel("A").point(lambda v: 255 if v > 16 else 0).getbbox()
        if bbox:
            cut = cut.crop(bbox)
        dest = a.out / (path.stem + ".png")
        cut.save(dest)
        print(f"{dest} {cut.size}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
