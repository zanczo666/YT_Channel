#!/usr/bin/env python3
"""Generator miniatur YouTube w stałym szablonie kanału (docs/YT_PUBLISHING_STANDARD.md §3).

Układ: tekst po lewej (~55%), twarz albo obraz po prawej (~42%), ciemne tło z siatką, etykieta filaru w rogu.
Kolor akcentu = werdykt: pass (zieleń), fail (czerwień), neutral (bursztyn).
Wynik: JPG 1280×720 ≤ 2 MB oraz podgląd 168×94 (rozmiar z listy na telefonie) do kontroli czytelności.

Wymaga Pillow (uruchamiać `python3`, nie `python3 -I`).

Przykład:
    python3 scripts/thumbnail.py --text "WHY NOT|*100%* STOCKS?" --label "PAPER vs REALITY" \\
        --verdict fail --face assets/face/face-skeptic.png --bg tlo.png --out content/thumbs/slug.jpg
Słowa w *gwiazdkach* dostają kolor akcentu; `|` łamie linię.
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

from PIL import Image, ImageDraw, ImageEnhance, ImageFilter, ImageFont, ImageOps

W, H = 1280, 720
FONT_BOLD = "/usr/share/fonts/opentype/urw-base35/NimbusSansNarrow-Bold.otf"
FONT_LABEL = "/usr/share/fonts/opentype/urw-base35/NimbusSans-Bold.otf"
BG = (13, 19, 30)
GRID = (30, 40, 56)
TEXT = (245, 247, 250)
ACCENTS = {"pass": (110, 231, 140), "fail": (255, 92, 92), "neutral": (255, 196, 61)}
MAX_BYTES = 2 * 1024 * 1024


def base_background(bg_path: Path | None) -> Image.Image:
    """Ciemne tło: podany obraz (przyciemniony, lekko rozmyty) albo gładkie tło z siatką."""
    if bg_path:
        img = ImageOps.fit(Image.open(bg_path).convert("RGB"), (W, H))
        img = img.filter(ImageFilter.GaussianBlur(2))
        img = ImageEnhance.Brightness(img).enhance(0.35)
    else:
        img = Image.new("RGB", (W, H), BG)
    d = ImageDraw.Draw(img)
    for x in range(0, W, 48):
        d.line([(x, 0), (x, H)], fill=GRID, width=1)
    for y in range(0, H, 48):
        d.line([(0, y), (W, y)], fill=GRID, width=1)
    return img


def place_face(img: Image.Image, face_path: Path, accent: tuple[int, int, int]) -> int:
    """Twarz po prawej: PNG z przezroczystością wklejany jako wycięcie, zwykłe zdjęcie przycinane do kadru.

    Zwraca współrzędną x lewej krawędzi twarzy — tekst nie może jej przekroczyć."""
    face = Image.open(face_path)
    box_w, box_h = int(W * 0.42), H
    if face.mode in ("RGBA", "LA") or "transparency" in face.info:
        face = face.convert("RGBA")
        face.thumbnail((box_w, int(box_h * 1.0)))
        # Obrys w kolorze akcentu — rozpoznawalność szablonu.
        alpha = face.split()[-1]
        outline = Image.new("RGBA", face.size, accent + (0,))
        outline.putalpha(alpha.filter(ImageFilter.MaxFilter(13)))
        x, y = W - face.width + 20, H - face.height
        img.paste(outline, (x, y), outline)
        img.paste(face, (x, y), face)
        return x
    else:
        face = ImageOps.fit(face.convert("RGB"), (box_w, box_h))
        mask = Image.linear_gradient("L").rotate(90).resize((box_w, box_h))  # miękkie przejście w tło
        img.paste(face, (W - box_w, 0), mask)
        return W - box_w


def parse_lines(text: str) -> list[list[tuple[str, bool]]]:
    """Linie słów z flagą akcentu; `*…*` może obejmować kilka słów, także przez `|`."""
    lines, hot = [], False
    for raw in text.split("|"):
        words = []
        for w in raw.split():
            if w.startswith("*"):
                hot = True
            words.append((w.strip("*"), hot))
            if w.endswith("*") and len(w) > 1:
                hot = False
        lines.append(words)
    return lines


def fit_font(lines, max_w: int, max_h: int) -> ImageFont.FreeTypeFont:
    for size in range(190, 40, -4):
        font = ImageFont.truetype(FONT_BOLD, size)
        widths = [font.getlength(" ".join(w for w, _ in ln)) for ln in lines]
        if max(widths) <= max_w and len(lines) * size * 1.02 <= max_h:
            return font
    return ImageFont.truetype(FONT_BOLD, 40)


def draw_text(img: Image.Image, text: str, accent, right_edge: int | None) -> None:
    d = ImageDraw.Draw(img)
    lines = parse_lines(text)
    left = 56
    max_w = (right_edge - left - 30) if right_edge else int(W * 0.88)
    font = fit_font(lines, max_w, int(H * 0.62))
    lh = int(font.size * 1.02)
    y = (H - lh * len(lines)) // 2 + 20
    space = font.getlength(" ")
    for ln in lines:
        x = left
        for word, hot in ln:
            # Cień dla czytelności na dowolnym tle.
            d.text((x + 4, y + 5), word, font=font, fill=(0, 0, 0))
            d.text((x, y), word, font=font, fill=accent if hot else TEXT)
            x += font.getlength(word) + space
        y += lh


def draw_label(img: Image.Image, label: str, accent) -> None:
    d = ImageDraw.Draw(img)
    font = ImageFont.truetype(FONT_LABEL, 30)
    pad = 14
    w = int(font.getlength(label)) + 2 * pad
    d.rectangle([40, 36, 40 + w, 36 + 30 + 2 * pad - 4], fill=accent)
    d.text((40 + pad, 36 + pad - 4), label, font=font, fill=BG)


def save_jpg(img: Image.Image, out: Path) -> None:
    out.parent.mkdir(parents=True, exist_ok=True)
    for q in (92, 88, 84, 80, 75, 70):
        img.save(out, "JPEG", quality=q, optimize=True)
        if out.stat().st_size <= MAX_BYTES:
            return
    raise RuntimeError(f"Miniatura > 2 MB nawet przy quality=70: {out}")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--text", required=True, help="2–4 słowa; *słowo* = akcent, | = nowa linia")
    ap.add_argument("--label", default="", help="etykieta filaru, np. 'GRAVEYARD #2'")
    ap.add_argument("--verdict", choices=ACCENTS, default="neutral")
    ap.add_argument("--face", type=Path)
    ap.add_argument("--bg", type=Path)
    ap.add_argument("--out", required=True, type=Path)
    a = ap.parse_args()

    words = len(re.findall(r"[^\s|*]+", a.text))
    if words > 5:
        print(f"UWAGA: {words} słów na miniaturze — standard to 2–4.", file=sys.stderr)
    accent = ACCENTS[a.verdict]
    img = base_background(a.bg)
    face_x = place_face(img, a.face, accent) if a.face else None
    draw_text(img, a.text, accent, right_edge=face_x)
    if a.label:
        draw_label(img, a.label.upper(), accent)
    save_jpg(img, a.out)
    preview = a.out.with_name(a.out.stem + "-podglad-168x94.png")
    img.resize((168, 94), Image.LANCZOS).save(preview)
    print(f"{a.out} ({a.out.stat().st_size // 1024} KB), podgląd: {preview}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
