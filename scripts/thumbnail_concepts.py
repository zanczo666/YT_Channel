#!/usr/bin/env python3
"""Alternatywne koncepcje miniatur — każda z inną kompozycją, paletą i typografią (wyjście poza jeden szablon
`thumbnail.py`). Do testów A/B i szukania stylu kanału.

Koncepcje (`--concept`):
- `paper`      — kremowe tło, przechylona strona publikacji z zakreśleniem i odręcznym kółkiem, tytuł szeryfowy.
                 Bez twarzy. Filar Paper vs Reality (w produkcji: realna strona PDF przez `--page`).
- `split`      — ekran dzielony: jasna połowa BACKTEST z gładką krzywą | ciemna połowa LIVE z załamaniem,
                 postrzępiony szew, twarz na szwie.
- `terminal`   — pełnoekranowy terminal, monospace, wielki werdykt z kursorem. Bez twarzy.
- `stamp`      — raport na biurku z wielką czerwoną pieczątką (Strategy Graveyard), twarz z boku.
- `minimal`    — białe tło, jedna cienka „zbyt idealna” linia i krótkie zdanie szeryfem (styl Veritasium).
- `closeup`    — bardzo duża twarz po lewej, ucięta krawędzią kadru; po prawej jeden obiekt i 2 słowa.
- `magnifier`  — piękna krzywa, a pod lupą poszarpana czerwona prawda. Bez twarzy.

Uwaga do `thumbnail_check.py`: OCR nie czyta tekstu obróconego (pieczątka) ani przeciętego liniami
(terminal) — przy tych koncepcjach FAIL na `ocr_small` bywa fałszywy; decyduje podgląd 168×94 w siatce.

Wszystkie wykresy są dekoracyjne: bez osi z wartościami i bez liczb (liczby wyłącznie z Ledgera / kart).
Słowa w *gwiazdkach* = akcent, `|` = nowa linia (jak w thumbnail.py).

Wymaga Pillow i fontów OFL/Apache w `--fonts` (domyślnie assets/fonts): DMSerifDisplay, IBMPlexMono, Anton,
SpecialElite, PermanentMarker.

Przykład:
    python3 scripts/thumbnail_concepts.py --concept split --face assets/face/cut/face-skeptic.png \\
        --verdict fail --out content/publish/<slug>/thumbnail-split.jpg
"""

from __future__ import annotations

import argparse
import math
import random
import sys
import zlib
from pathlib import Path

from PIL import Image, ImageChops, ImageDraw, ImageEnhance, ImageFilter, ImageFont, ImageOps

import thumbnail as base

W, H = base.W, base.H
RED, GREEN, AMBER = (226, 56, 48), (34, 160, 90), (240, 170, 30)
FONTS = Path("assets/fonts")


def font(name: str, size: int) -> ImageFont.FreeTypeFont:
    files = {"serif": "DMSerifDisplay-Regular.ttf", "serif-i": "DMSerifDisplay-Italic.ttf",
             "mono": "IBMPlexMono-Regular.ttf", "mono-b": "IBMPlexMono-Bold.ttf", "anton": "Anton-Regular.ttf",
             "type": "SpecialElite-Regular.ttf", "marker": "PermanentMarker-Regular.ttf"}
    return ImageFont.truetype(str(FONTS / files[name]), size)


def fit(name: str, lines: list[str], max_w: int, max_h: int, start: int = 220) -> ImageFont.FreeTypeFont:
    for size in range(start, 30, -4):
        f = font(name, size)
        _, cap, lh = base.line_metrics(f)
        if max(f.getlength(ln) for ln in lines) <= max_w and (len(lines) - 1) * lh + cap <= max_h:
            return f
    return font(name, 30)


def draw_lines(img, text: str, fname: str, box, color, accent, shadow=None, align="left") -> tuple[int, int]:
    """Tekst w ramce (x0, y0, x1, y1), dopasowany rozmiarem; *słowa* w akcencie. Zwraca (dół, prawy brzeg)."""
    lines = base.parse_lines(text)
    plain = [" ".join(w for w, _ in ln) for ln in lines]
    x0, y0, x1, y1 = box
    f = fit(fname, plain, x1 - x0, y1 - y0)
    top, cap, lh = base.line_metrics(f)
    d = ImageDraw.Draw(img)
    y, space, right = y0 - top, f.getlength(" "), x0
    for ln, txt in zip(lines, plain):
        x = x0 if align == "left" else x1 - f.getlength(txt)
        for word, hot in ln:
            if shadow:
                d.text((x + 4, y + 5), word, font=f, fill=shadow)
            d.text((x, y), word, font=f, fill=accent if hot else color)
            x += f.getlength(word) + space
        right = max(right, x - space)
        y += lh
    return y - lh + top + cap, int(right)


def paste_shadow(img: Image.Image, layer: Image.Image, xy, blur=18, offset=(10, 16), alpha=150) -> None:
    sh = Image.new("RGBA", layer.size, (0, 0, 0, 0))
    sh.putalpha(layer.getchannel("A").point(lambda v: v * alpha // 255))
    pad = blur * 3
    big = Image.new("RGBA", (layer.width + 2 * pad, layer.height + 2 * pad), (0, 0, 0, 0))
    big.paste(sh, (pad, pad))
    big = big.filter(ImageFilter.GaussianBlur(blur))
    img.paste(big, (xy[0] - pad + offset[0], xy[1] - pad + offset[1]), big)
    img.paste(layer, xy, layer)


def curve(verdict: str, n: int, seed: int, split: float = 0.6) -> list[float]:
    return base.equity_path(verdict, n, seed, None, split)


def polyline(d, pts, color, width):
    d.line(pts, fill=color, width=width, joint="curve")


def greek(d, x, y, w, n, lh, color, rnd, last_short=True):
    """Udawany tekst akapitu (szare paski) — bez treści i bez liczb."""
    for i in range(n):
        lw = w if (i < n - 1 or not last_short) else int(w * rnd.uniform(0.35, 0.7))
        lw = int(lw * rnd.uniform(0.92, 1.0))
        d.rounded_rectangle([x, y + i * lh, x + lw, y + i * lh + lh * 0.42], 3, fill=color)


def face_layer(path: Path, max_w: int, max_h: int, accent, zoom=True, grade=True) -> Image.Image:
    base.FACE_ZOOM = zoom
    f = base.load_face(path).convert("RGBA")
    f = base.fit_into(f, max_w, max_h)
    return base.grade_face(f, accent) if grade else f


# --- koncepcje ------------------------------------------------------------------


def on_light(accent) -> tuple[int, int, int]:
    """Akcent przyciemniony do jasnego tła — czerwień marki na kremowym/białym ma tylko ~3,5:1 kontrastu."""
    return tuple(int(c * 0.72) for c in accent)


def c_paper(a, accent, rnd) -> Image.Image:
    accent = on_light(accent)
    img = Image.new("RGB", (W, H), (240, 234, 220))
    noise = Image.effect_noise((W, H), 18).convert("RGB")
    img = Image.blend(img, ImageChops.multiply(img, noise.point(lambda v: 200 + v // 5)), 0.35)
    # Strona publikacji
    pw, ph = 600, 820
    page = Image.new("RGBA", (pw, ph), (252, 251, 247, 255))
    d = ImageDraw.Draw(page)
    if a.page:
        page.paste(ImageOps.fit(Image.open(a.page).convert("RGB"), (pw, ph), centering=(0.5, 0.0)), (0, 0))
    else:
        d.text((48, 40), a.sub or "Working Paper", font=font("serif", 40), fill=(30, 30, 30))
        greek(d, 48, 104, 420, 2, 26, (150, 150, 150), rnd)
        d.text((48, 176), "Abstract", font=font("serif-i", 26), fill=(60, 60, 60))
        greek(d, 48, 220, 504, 6, 28, (185, 185, 185), rnd)
        # zakreślone zdanie (teza)
        d.rectangle([44, 220 + 6 * 28 + 8, 552, 220 + 6 * 28 + 34], fill=(255, 226, 80))
        greek(d, 48, 220 + 6 * 28 + 14, 500, 1, 28, (90, 90, 90), rnd, last_short=False)
        greek(d, 48, 440, 504, 9, 28, (185, 185, 185), rnd)
    # odręczne kółko wokół tezy
    ring = Image.new("RGBA", (pw, ph), (0, 0, 0, 0))
    rd = ImageDraw.Draw(ring)
    cy = 220 + 6 * 28 + 21
    for k, dx in enumerate((0, 5)):
        rd.ellipse([18 + dx, cy - 40 + k * 3, 586 - dx, cy + 38 - k * 2], outline=accent + (235,), width=7)
    page.alpha_composite(ring)
    page = page.rotate(-5, resample=Image.BICUBIC, expand=True)
    paste_shadow(img, page, (40, 40))
    # Tekst po prawej — szeryf, ciemny
    bottom, _ = draw_lines(img, a.text, "serif", (740, 70, 1240, 400), (25, 25, 28), accent)
    # Odręczny dopisek pod tytułem
    if a.note:
        d = ImageDraw.Draw(img)
        d.text((748, bottom + 50), a.note, font=font("marker", 64), fill=accent)
    return img


def c_split(a, accent, rnd) -> Image.Image:
    img = Image.new("RGB", (W, H), (236, 242, 238))
    dark = Image.new("RGB", (W, H), (16, 16, 20))
    # postrzępiony szew
    mx = W // 2
    pts = [(mx + rnd.randint(-18, 18), y) for y in range(0, H + 40, 40)]
    mask = Image.new("L", (W, H), 0)
    ImageDraw.Draw(mask).polygon(pts + [(W, H), (W, 0)], fill=255)
    img.paste(dark, (0, 0), mask)
    d = ImageDraw.Draw(img)
    ys = curve("fail", 160, rnd.randint(0, 10**6), 0.5)
    xs = [40 + (W - 80) * i / (len(ys) - 1) for i in range(len(ys))]
    top, bot = 170, 640
    pts_c = [(x, bot - (bot - top) * y) for x, y in zip(xs, ys)]
    half = len(pts_c) // 2
    polyline(d, pts_c[:half + 1], GREEN, 9)
    polyline(d, pts_c[half:], RED, 9)
    lab = font("anton", 120)
    d.text((48, 26), "BACKTEST", font=lab, fill=(20, 60, 40))
    lw = lab.getlength(a.sub or "LIVE")
    d.text((W - 48 - lw, 26), a.sub or "LIVE", font=lab, fill=RED)
    d.line(pts, fill=(255, 255, 255), width=6)
    if a.face:
        f = face_layer(a.face, 520, 470, accent)
        outline = Image.new("RGBA", f.size, (255, 255, 255, 0))
        outline.putalpha(f.getchannel("A").point(lambda v: 255 if v > 90 else 0).filter(ImageFilter.MaxFilter(11)))
        x = mx - f.width // 2
        img.paste(outline, (x, H - f.height), outline)
        img.paste(f, (x, H - f.height), f)
    return img


def c_terminal(a, accent, rnd) -> Image.Image:
    img = Image.new("RGB", (W, H), (8, 10, 9))
    d = ImageDraw.Draw(img)
    d.rectangle([0, 0, W, 54], fill=(28, 30, 32))
    for i, c in enumerate([(255, 95, 86), (255, 189, 46), (39, 201, 63)]):
        d.ellipse([22 + i * 30, 18, 40 + i * 30, 36], fill=c)
    d.text((W // 2 - 140, 12), "research — bash", font=font("mono", 26), fill=(150, 155, 160))
    small = font("mono", 30)
    dim = (70, 150, 90)
    lines = a.sub.split("|") if a.sub else ["$ python validate.py --out-of-sample", "loading data ...",
                                             "walk-forward ........ done", "costs + slippage ..... done"]
    for i, ln in enumerate(lines):
        d.text((48, 96 + i * 46), ln, font=small, fill=dim)
    bottom, right = draw_lines(img, a.text, "mono-b", (48, 330, 1200, 640), accent, accent)
    # kursor
    d.rectangle([right + 24, bottom - 120, right + 84, bottom], fill=(220, 230, 220))
    # scanlines + lekka poświata tekstu
    glow = img.filter(ImageFilter.GaussianBlur(10))
    img = ImageChops.screen(img, ImageEnhance.Brightness(glow).enhance(0.6))
    sl = Image.new("L", (W, H), 0)
    sd = ImageDraw.Draw(sl)
    for y in range(0, H, 4):
        sd.line([(0, y), (W, y)], fill=40)
    img.paste((0, 0, 0), (0, 0), sl)
    return img


def c_stamp(a, accent, rnd) -> Image.Image:
    img = Image.new("RGB", (W, H), (58, 62, 68))
    vign = Image.radial_gradient("L").resize((W, H)).point(lambda v: int(v * 0.8))
    img.paste((20, 22, 26), (0, 0), vign)
    sw, sh = 820, 900
    sheet = Image.new("RGBA", (sw, sh), (246, 243, 234, 255))
    d = ImageDraw.Draw(sheet)
    d.text((50, 44), "STRATEGY REVIEW", font=font("type", 46), fill=(40, 40, 40))
    d.text((50, 104), a.sub or "Candidate: QF-xxx", font=font("type", 30), fill=(90, 90, 90))
    d.line([(50, 150), (sw - 50, 150)], fill=(60, 60, 60), width=2)
    # wykres w ramce
    bx0, by0, bx1, by1 = 50, 180, sw - 50, 520
    d.rectangle([bx0, by0, bx1, by1], outline=(80, 80, 80), width=2)
    ys = curve("fail", 120, rnd.randint(0, 10**6), 0.6)
    pts = [(bx0 + 20 + (bx1 - bx0 - 40) * i / (len(ys) - 1), by1 - 20 - (by1 - by0 - 60) * y) for i, y in enumerate(ys)]
    polyline(d, pts, (30, 30, 30), 4)
    greek(d, 50, 560, sw - 100, 8, 34, (175, 172, 165), rnd)
    sheet = sheet.rotate(4, resample=Image.BICUBIC, expand=True)
    paste_shadow(img, sheet, (-30, 20))
    # pieczątka
    word = a.text.replace("*", "").replace("|", " ")
    sf = font("anton", 150)
    tw = int(sf.getlength(word))
    st = Image.new("RGBA", (tw + 80, 230), (0, 0, 0, 0))
    sd = ImageDraw.Draw(st)
    sd.rounded_rectangle([6, 6, tw + 74, 224], 18, outline=RED + (255,), width=12)
    sd.text((40, 20), word, font=sf, fill=RED + (255,))
    wear = Image.effect_noise(st.size, 90).point(lambda v: 0 if v < 70 else 255)
    st.putalpha(ImageChops.multiply(st.getchannel("A"), wear.filter(ImageFilter.GaussianBlur(0.6))))
    st = st.rotate(14, resample=Image.BICUBIC, expand=True)
    img.paste(st, (70, 230), st)
    if a.face:
        f = face_layer(a.face, 470, 640, accent)
        paste_shadow(img, f, (W - f.width + 10, H - f.height), blur=24, offset=(-14, 0), alpha=170)
    return img


def c_minimal(a, accent, rnd) -> Image.Image:
    accent = on_light(accent)
    img = Image.new("RGB", (W, H), (247, 246, 242))
    d = ImageDraw.Draw(img)
    # jedna „zbyt idealna” linia: prawie prosta, rosnąca
    n, pts = 120, []
    for i in range(n):
        t = i / (n - 1)
        pts.append((140 + 1000 * t, 640 - 430 * t + rnd.gauss(0, 1.2)))
    polyline(d, pts, (20, 20, 22), 6)
    ex, ey = pts[-1]
    d.ellipse([ex - 16, ey - 16, ex + 16, ey + 16], fill=accent)
    draw_lines(img, a.text, "serif", (70, 50, 1000, 300), (20, 20, 22), accent)
    if a.label:
        lf = font("mono-b", 26)
        d.text((72, H - 70), a.label.upper(), font=lf, fill=(120, 120, 120))
    return img


def c_closeup(a, accent, rnd) -> Image.Image:
    img = Image.new("RGB", (W, H), (14, 18, 26))
    glow = Image.new("RGB", (W, H), accent)
    m = Image.new("L", (W, H), 0)
    ImageDraw.Draw(m).ellipse([700, 330, 1420, 900], fill=90)   # poświata za kartą, nie za tekstem
    img.paste(glow, (0, 0), m.filter(ImageFilter.GaussianBlur(140)))
    if a.face:
        f = face_layer(a.face, 900, int(H * 1.35), accent)
        x, y = -int(f.width * 0.18), H - f.height + int(f.height * 0.12)
        img.paste(f, (x, y), f)
        edge = x + f.width
    else:
        edge = 560
    # jeden obiekt: mała karta z załamaniem
    panel = base.synthetic_panel((460, 270), a.verdict, accent, rnd.randint(0, 10**6), None, a.label.upper())
    base.place_card(img, panel, (max(edge - 40, 700), 360, max(edge - 40, 700) + 460, 630), accent, angle=4)
    draw_lines(img, a.text, "anton", (max(edge - 20, 690), 70, 1230, 300), (245, 247, 250), accent,
               shadow=(0, 0, 0))
    return img


def c_magnifier(a, accent, rnd) -> Image.Image:
    img = Image.new("RGB", (W, H), (10, 22, 34))
    d = ImageDraw.Draw(img)
    seed = rnd.randint(0, 10**6)
    smooth = curve("pass", 200, seed, 1.0)
    xs = [60 + (W - 120) * i / 199 for i in range(200)]
    top, bot = 240, 650
    pts = [(x, bot - (bot - top) * y) for x, y in zip(xs, smooth)]
    polyline(d, pts, GREEN, 8)
    # lupa
    cx, cy, r = 840, 420, 190
    lens = Image.new("RGB", (W, H), (24, 10, 14))
    ld = ImageDraw.Draw(lens)
    jag = [(x, y + rnd.gauss(0, 1) * 34 + 60 * math.sin(i / 3.0)) for i, (x, y) in enumerate(pts)]
    zoom = [(cx + (x - cx) * 1.8, cy + (y - cy) * 1.8) for x, y in jag]
    polyline(ld, zoom, RED, 9)
    m = Image.new("L", (W, H), 0)
    ImageDraw.Draw(m).ellipse([cx - r, cy - r, cx + r, cy + r], fill=255)
    img.paste(lens, (0, 0), m)
    d = ImageDraw.Draw(img)
    ang = math.radians(45)
    hx0, hy0 = cx + (r + 10) * math.cos(ang), cy + (r + 10) * math.sin(ang)
    d.line([(hx0, hy0), (hx0 + 150 * math.cos(ang), hy0 + 150 * math.sin(ang))], fill=(200, 205, 215), width=34)
    d.ellipse([cx - r - 14, cy - r - 14, cx + r + 14, cy + r + 14], outline=(220, 225, 235), width=22)
    draw_lines(img, a.text, "anton", (56, 40, 640, 330), (245, 247, 250), accent, shadow=(0, 0, 0))
    return img


CONCEPTS = {"paper": c_paper, "split": c_split, "terminal": c_terminal, "stamp": c_stamp,
            "minimal": c_minimal, "closeup": c_closeup, "magnifier": c_magnifier}


def main() -> int:
    global FONTS
    ap = argparse.ArgumentParser()
    ap.add_argument("--concept", required=True, choices=CONCEPTS)
    ap.add_argument("--text", required=True, help="2–4 słowa; *słowo* = akcent, | = nowa linia")
    ap.add_argument("--sub", default="", help="tekst pomocniczy (tytuł publikacji, etykieta LIVE, linie terminala)")
    ap.add_argument("--note", default="", help="paper: odręczny dopisek")
    ap.add_argument("--label", default="")
    ap.add_argument("--verdict", choices=base.ACCENTS, default="fail")
    ap.add_argument("--face", type=Path)
    ap.add_argument("--page", type=Path, help="paper: obraz prawdziwej strony publikacji")
    ap.add_argument("--fonts", type=Path, default=FONTS)
    ap.add_argument("--out", required=True, type=Path)
    a = ap.parse_args()
    FONTS = a.fonts
    accent = {"fail": RED, "pass": GREEN, "neutral": AMBER}[a.verdict]
    rnd = random.Random(zlib.crc32((a.concept + a.text).encode()))
    img = CONCEPTS[a.concept](a, accent, rnd).convert("RGB")
    base.save_jpg(img, a.out)
    print(a.out)
    return 0


if __name__ == "__main__":
    sys.exit(main())
