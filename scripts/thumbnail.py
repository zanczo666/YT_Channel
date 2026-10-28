#!/usr/bin/env python3
"""Generator miniatur YouTube w stałym szablonie kanału (docs/YT_PUBLISHING_STANDARD.md §3).

Układ: tekst po lewej (~55%), twarz albo obraz po prawej (~42%), ciemne tło z siatką, etykieta filaru w rogu.
Kolor akcentu = werdykt: pass (zieleń), fail (czerwień), neutral (bursztyn).
Wynik: JPG 1280×720 ≤ 2 MB oraz podgląd 168×94 (rozmiar z listy na telefonie) do kontroli czytelności.

Motyw w tle (`--motif`), rysowany pod tekstem i twarzą, przyciemniony po stronie tekstu:
- `equity` — krzywa kapitału z linią podziału IN-SAMPLE / OUT-OF-SAMPLE (fail: załamanie po OOS, pass: wzrost),
- `candles` — świece z tym samym przebiegiem, `funnel` — słupki lejka malejące etap po etapie, `none`.
Motyw jest dekoracyjny: bez osi z wartościami i bez liczb. Realny przebieg: `--equity-csv` (jedna kolumna equity).

Wymaga Pillow (uruchamiać `python3`, nie `python3 -I`).

Przykład:
    python3 scripts/thumbnail.py --text "WHY NOT|*100%* STOCKS?" --label "PAPER vs REALITY" \\
        --verdict fail --face assets/face/face-skeptic.png --bg tlo.png --out content/thumbs/slug.jpg
Słowa w *gwiazdkach* dostają kolor akcentu; `|` łamie linię.
"""

from __future__ import annotations

import argparse
import csv
import random
import re
import sys
import zlib
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


def equity_path(verdict: str, n: int, seed: int, csv_path: Path | None, split: float) -> list[float]:
    """Przebieg krzywej 0..1: z pliku CSV (realne dane) albo syntetyczny wg werdyktu (tylko dekoracja)."""
    if csv_path:
        with csv_path.open(encoding="utf-8") as fh:
            vals = [float(r[0]) for r in csv.reader(fh) if r and re.match(r"^-?[\d.]+$", r[0].strip())]
        step = max(1, len(vals) // n)
        vals = vals[::step]
    else:
        rnd, v, vals = random.Random(seed), 0.0, []
        cut = int(n * split)
        for i in range(n):
            drift = 0.9 if i < cut else {"fail": -1.6, "pass": 0.8, "neutral": 0.0}[verdict]
            v += drift + rnd.gauss(0, 1.6)
            vals.append(v)
    lo, hi = min(vals), max(vals)
    return [(x - lo) / (hi - lo or 1) for x in vals]


def draw_motif(img: Image.Image, motif: str, verdict: str, accent, seed: int, csv_path: Path | None,
               right_limit: int | None) -> None:
    """Motyw tradingowy w tle + przyciemnienie lewej strony pod tekst.

    `right_limit` = lewa krawędź twarzy: kluczowa część motywu (podział IS/OOS, koniec lejka) musi być przed nią."""
    if motif == "none":
        return
    layer = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(layer)
    top, bottom, x0, x1 = int(H * 0.22), int(H * 0.88), 0, W
    split = (right_limit * 0.82 / W) if right_limit else 0.62
    split_x = x0 + int((x1 - x0) * split)
    if motif in ("equity", "candles"):
        pts_n = 46 if motif == "candles" else 160
        ys = equity_path(verdict, pts_n, seed, csv_path, split)
        xs = [x0 + (x1 - x0) * i / (len(ys) - 1) for i in range(len(ys))]
        py = [bottom - (bottom - top) * y for y in ys]
        if motif == "equity":
            d.polygon([(xs[0], bottom)] + list(zip(xs, py)) + [(xs[-1], bottom)], fill=accent + (38,))
            glow = Image.new("RGBA", (W, H), (0, 0, 0, 0))
            ImageDraw.Draw(glow).line(list(zip(xs, py)), fill=accent + (170,), width=14, joint="curve")
            layer.alpha_composite(glow.filter(ImageFilter.GaussianBlur(10)))
            d.line(list(zip(xs, py)), fill=accent + (235,), width=5, joint="curve")
        else:
            rnd, cw = random.Random(seed + 1), (x1 - x0) / len(ys) * 0.6
            for i in range(1, len(ys)):
                o, c = py[i - 1], py[i]
                hi_, lo_ = min(o, c) - rnd.uniform(4, 22), max(o, c) + rnd.uniform(4, 22)
                col = (110, 231, 140, 150) if c < o else (255, 92, 92, 150)
                d.line([(xs[i], hi_), (xs[i], lo_)], fill=col, width=2)
                d.rectangle([xs[i] - cw / 2, min(o, c), xs[i] + cw / 2, max(o, c) + 2], fill=col)
        # Linia podziału próbki — znak rozpoznawczy „laboratorium backtestów”.
        lab = ImageFont.truetype(FONT_LABEL, 20)
        for y in range(top - 30, bottom, 18):
            d.line([(split_x, y), (split_x, y + 9)], fill=(200, 210, 225, 150), width=2)
        d.text((split_x - 14 - lab.getlength("IN-SAMPLE"), top - 30), "IN-SAMPLE", font=lab, fill=(200, 210, 225, 170))
        d.text((split_x + 14, top - 30), "OUT-OF-SAMPLE", font=lab, fill=(200, 210, 225, 170))
    elif motif == "funnel":
        stages = [1.0, 0.62, 0.38, 0.2, 0.09]
        fx0, fx1 = W * 0.04, (right_limit - 24) if right_limit else W * 0.96
        bw = (fx1 - fx0) / (len(stages) * 1.35)
        gap = bw * 0.35
        for i, f in enumerate(stages):
            bx = fx0 + i * (bw + gap)
            alpha = 210 if i == len(stages) - 1 else 90
            d.rectangle([bx, bottom - (bottom - top) * f, bx + bw, bottom], fill=accent + (alpha,))
    img.paste(layer, (0, 0), layer)
    # Przyciemnienie lewej części, żeby tekst zawsze był czytelny.
    shade = Image.linear_gradient("L").rotate(90).resize((W, H)).point(lambda v: int(v * 0.85))
    img.paste(Image.new("RGB", (W, H), BG), (0, 0), shade.transpose(Image.FLIP_LEFT_RIGHT))


def face_left_x(face_path: Path) -> int:
    """Lewa krawędź twarzy po umieszczeniu w kadrze (ta sama geometria co place_face)."""
    face = Image.open(face_path)
    box_w = int(W * 0.42)
    if face.mode in ("RGBA", "LA") or "transparency" in face.info:
        face = face.copy()
        face.thumbnail((box_w, H))
        return W - face.width + 20
    return W - box_w


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
    ap.add_argument("--motif", choices=["equity", "candles", "funnel", "none"], default="equity")
    ap.add_argument("--equity-csv", type=Path, help="realna krzywa kapitału (jedna kolumna)")
    ap.add_argument("--out", required=True, type=Path)
    a = ap.parse_args()

    words = len(re.findall(r"[^\s|*]+", a.text))
    if words > 5:
        print(f"UWAGA: {words} słów na miniaturze — standard to 2–4.", file=sys.stderr)
    accent = ACCENTS[a.verdict]
    img = base_background(a.bg)
    draw_motif(img, a.motif, a.verdict, accent, zlib.crc32(a.text.encode()), a.equity_csv,
               face_left_x(a.face) if a.face else None)
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
