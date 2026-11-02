#!/usr/bin/env python3
"""Wycinanie tła ze zdjęć twarzy (lokalnie, rembg — zdjęcia nie opuszczają serwera).

Obraca wg EXIF, zmniejsza do max 1600 px wysokości, usuwa tło, przycina do sylwetki i zapisuje PNG
z przezroczystością. Uruchamiać interpreterem z venv, w którym jest rembg:

    /home/claude/.venvs/rembg/bin/python scripts/face_cutout.py --out assets/face/cut assets/face/raw/*.jpg

`--defringe N` (domyślnie 3) usuwa jasną obwódkę z tła zdjęcia na krawędzi sylwetki: zwęża maskę o N px
i barwi pas krawędzi kolorem z wnętrza sylwetki. Modele i pamięć (test 2026-10-30, zdjęcie 1200×1600):
`u2net_human_seg` ~0,9 GB, `isnet-general-use` ~1,1 GB, `birefnet-general-lite` ~7,6 GB, `birefnet-portrait`
~9,3 GB — na VPS (7 GB, sesje Claude Code) tylko dwa pierwsze.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

import cv2  # zależność rembg
import numpy as np
from PIL import Image, ImageFilter, ImageOps
from rembg import new_session, remove

MAX_H = 1600


def defringe(cut: Image.Image, px: int) -> Image.Image:
    """Zwęża maskę o `px` i zastępuje kolor pasa krawędzi kolorem „wylanym” z wnętrza sylwetki."""
    rgb = np.asarray(cut.convert("RGB"), dtype=np.float32)
    alpha = cut.getchannel("A")
    inner = np.asarray(alpha.point(lambda v: 255 if v > 200 else 0)
                       .filter(ImageFilter.MinFilter(2 * (px + 2) + 1)), dtype=np.float32) / 255
    radius = 3 * px + 4
    blur = lambda a: cv2.GaussianBlur(a.astype(np.float32), (0, 0), radius)
    weight = blur(inner)
    fill = np.stack([blur(rgb[..., c] * inner) for c in range(3)], -1) / np.maximum(weight, 1e-4)[..., None]
    band = (inner < 1)[..., None]
    out = np.where(band, fill, rgb).clip(0, 255).astype(np.uint8)
    new_alpha = alpha.filter(ImageFilter.MinFilter(2 * px + 1)).filter(ImageFilter.GaussianBlur(0.8))
    res = Image.fromarray(out, "RGB").convert("RGBA")
    res.putalpha(new_alpha)
    return res


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", required=True, type=Path)
    ap.add_argument("--model", default="u2net_human_seg", help="np. u2net_human_seg, isnet-general-use")
    ap.add_argument("--defringe", type=int, default=3, help="px zwężenia maski i czyszczenia krawędzi (0 = wyłącz)")
    ap.add_argument("images", nargs="+", type=Path)
    a = ap.parse_args()

    a.out.mkdir(parents=True, exist_ok=True)
    session = new_session(a.model)
    for path in a.images:
        img = ImageOps.exif_transpose(Image.open(path)).convert("RGB")
        if img.height > MAX_H:
            img.thumbnail((MAX_H * 2, MAX_H))
        cut = remove(img, session=session, post_process_mask=True)
        if a.defringe:
            cut = defringe(cut, a.defringe)
        bbox = cut.getchannel("A").point(lambda v: 255 if v > 16 else 0).getbbox()
        if bbox:
            cut = cut.crop(bbox)
        dest = a.out / (path.stem + ".png")
        cut.save(dest)
        print(f"{dest} {cut.size}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
