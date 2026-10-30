#!/usr/bin/env python3
"""Makieta feedu YouTube: nasze warianty miniatur obok innych miniatur, z tytułem, kanałem i znacznikiem czasu,
w trybie ciemnym i jasnym (docs/YT_PUBLISHING_STANDARD.md §3). Odpowiada na pytanie „czy się wyróżnia”,
a nie tylko „czy jest ładna”.

Dwa widoki na jednym arkuszu (osobno dla trybu ciemnego i jasnego):
- strona główna (siatka 3 kolumny, miniatura 360×203),
- lista „Up next” / wyniki na telefonie (miniatura 168×94, tytuł obok).

Inne miniatury (`--others`): np. aktualne miniatury kanałów z docs/research/ pobrane lokalnie (poza repo).
Tytuł bierze się z nazwy pliku (`_` → spacja). Bez `--others` makieta pokazuje same nasze warianty.

Wymaga Pillow (uruchamiać `python3`, nie `python3 -I`).

Użycie:
    python3 scripts/thumbnail_feed.py --title "Why a profitable backtest proves almost nothing" \\
        --channel "Imię Nazwisko" --duration 12:40 --others ~/yt-research/thumbs/*.jpg \\
        --out content/publish/<slug>/feed.png content/publish/<slug>/thumbnail-*.jpg
"""

from __future__ import annotations

import argparse
import random
import sys
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

FONT = "/usr/share/fonts/opentype/urw-base35/NimbusSans-Regular.otf"
FONT_BOLD = "/usr/share/fonts/opentype/urw-base35/NimbusSans-Bold.otf"
THEMES = {
    "dark": {"bg": (15, 15, 15), "title": (241, 241, 241), "meta": (170, 170, 170), "mark": (62, 166, 255)},
    "light": {"bg": (255, 255, 255), "title": (15, 15, 15), "meta": (96, 96, 96), "mark": (6, 95, 212)},
}
GRID_T, LIST_T = (360, 203), (168, 94)


def rounded(img: Image.Image, size, radius: int) -> Image.Image:
    img = img.convert("RGB").resize(size, Image.LANCZOS)
    mask = Image.new("L", size, 0)
    ImageDraw.Draw(mask).rounded_rectangle([0, 0, size[0] - 1, size[1] - 1], radius, fill=255)
    out = Image.new("RGBA", size, (0, 0, 0, 0))
    out.paste(img, (0, 0), mask)
    return out


def badge(d: ImageDraw.ImageDraw, x1: int, y1: int, text: str, scale: float) -> None:
    """Znacznik czasu w prawym dolnym rogu — dokładnie tam, gdzie YouTube zasłania miniaturę."""
    f = ImageFont.truetype(FONT_BOLD, max(9, int(12 * scale)))
    w = f.getlength(text) + 8 * scale
    h = 18 * scale
    d.rounded_rectangle([x1 - 4 * scale - w, y1 - 4 * scale - h, x1 - 4 * scale, y1 - 4 * scale], int(4 * scale),
                        fill=(0, 0, 0, 210))
    d.text((x1 - 4 * scale - w + 4 * scale, y1 - 4 * scale - h + 2 * scale), text, font=f, fill=(255, 255, 255))


def wrap(text: str, font, max_w: int, max_lines: int) -> list[str]:
    lines, cur = [], ""
    for word in text.split():
        trial = (cur + " " + word).strip()
        if font.getlength(trial) <= max_w:
            cur = trial
        else:
            lines.append(cur)
            cur = word
            if len(lines) == max_lines:
                break
    if len(lines) < max_lines and cur:
        lines.append(cur)
    if len(lines) == max_lines and " ".join(lines) != text:
        while font.getlength(lines[-1] + "…") > max_w and " " in lines[-1]:
            lines[-1] = lines[-1].rsplit(" ", 1)[0]
        lines[-1] += "…"
    return lines


def card_grid(sheet, d, x, y, thumb, title, channel, duration, theme, ours) -> None:
    t = THEMES[theme]
    sheet.paste(rounded(thumb, GRID_T, 12), (x, y), rounded(thumb, GRID_T, 12))
    badge(d, x + GRID_T[0], y + GRID_T[1], duration, 1.0)
    d.ellipse([x, y + GRID_T[1] + 12, x + 36, y + GRID_T[1] + 48], fill=t["mark"] if ours else t["meta"])
    ft = ImageFont.truetype(FONT_BOLD, 16)
    ty = y + GRID_T[1] + 12
    for ln in wrap(title, ft, GRID_T[0] - 50, 2):
        d.text((x + 48, ty), ln, font=ft, fill=t["title"])
        ty += 21
    d.text((x + 48, ty + 4), channel, font=ImageFont.truetype(FONT, 14), fill=t["meta"])


def card_list(sheet, d, x, y, thumb, title, channel, duration, theme) -> None:
    t = THEMES[theme]
    im = rounded(thumb, LIST_T, 8)
    sheet.paste(im, (x, y), im)
    badge(d, x + LIST_T[0], y + LIST_T[1], duration, 0.75)
    ft = ImageFont.truetype(FONT_BOLD, 14)
    ty = y + 2
    for ln in wrap(title, ft, 190, 2):
        d.text((x + LIST_T[0] + 10, ty), ln, font=ft, fill=t["title"])
        ty += 18
    d.text((x + LIST_T[0] + 10, ty + 4), channel, font=ImageFont.truetype(FONT, 12), fill=t["meta"])


def render(theme: str, ours: list[Path], others: list[Path], a) -> Image.Image:
    rnd = random.Random(7)
    items = [(p, a.title, a.channel, a.duration, True) for p in ours]
    items += [(p, p.stem.replace("_", " "), "", f"{rnd.randint(8, 25)}:{rnd.randint(0, 59):02d}", False)
              for p in others]
    # Nasze warianty rozproszone między innymi, nie zgrupowane w pierwszym rzędzie.
    if others:
        rnd.shuffle(items)
    cols, gap = 3, 24
    rows = (len(items) + cols - 1) // cols
    grid_h = rows * (GRID_T[1] + 80)
    list_n = min(len(items), 6)
    width = cols * (GRID_T[0] + gap) + gap + 400
    height = max(grid_h + 2 * gap + 30, list_n * (LIST_T[1] + 12) + 2 * gap + 30)
    sheet = Image.new("RGB", (width, height), THEMES[theme]["bg"])
    d = ImageDraw.Draw(sheet, "RGBA")
    hf = ImageFont.truetype(FONT_BOLD, 14)
    d.text((gap, 8), f"{theme.upper()} · strona główna", font=hf, fill=THEMES[theme]["meta"])
    lx = cols * (GRID_T[0] + gap) + gap
    d.text((lx, 8), "telefon · lista 168×94", font=hf, fill=THEMES[theme]["meta"])
    for i, (p, title, ch, dur, mine) in enumerate(items):
        thumb = Image.open(p)
        card_grid(sheet, d, gap + (i % cols) * (GRID_T[0] + gap), 34 + (i // cols) * (GRID_T[1] + 80),
                  thumb, title, ch or (a.channel if mine else "other channel"), dur, theme, mine)
        if i < list_n:
            card_list(sheet, d, lx, 34 + i * (LIST_T[1] + 12), thumb, title,
                      ch or (a.channel if mine else "other channel"), dur, theme)
    return sheet


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--title", required=True, help="tytuł filmu (EN) — taki, jak będzie pod miniaturą")
    ap.add_argument("--channel", default="Imię Nazwisko")
    ap.add_argument("--duration", default="12:00")
    ap.add_argument("--others", nargs="*", type=Path, default=[], help="inne miniatury do feedu")
    ap.add_argument("--out", required=True, type=Path)
    ap.add_argument("images", nargs="+", type=Path, help="nasze warianty")
    a = ap.parse_args()

    dark, light = render("dark", a.images, a.others, a), render("light", a.images, a.others, a)
    sheet = Image.new("RGB", (dark.width, dark.height + light.height))
    sheet.paste(dark, (0, 0))
    sheet.paste(light, (0, dark.height))
    a.out.parent.mkdir(parents=True, exist_ok=True)
    sheet.save(a.out)
    print(a.out)
    return 0


if __name__ == "__main__":
    sys.exit(main())
