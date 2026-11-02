#!/usr/bin/env python3
"""Złożone sceny miniatur renderowane z HTML/SVG przez Chromium (Playwright) — perspektywa 3D, szkło, setki
ścieżek, warstwy, mgła. Uzupełnia `thumbnail.py` (szablon) i `thumbnail_concepts.py` (proste koncepcje Pillow).

Sceny (`--scene`):
- `montecarlo` — setki symulowanych ścieżek kapitału, jedna podświetlona („twój backtest”) na skraju rozkładu,
                 histogram wyników z boku. Pytanie: szczęście czy przewaga?
- `landscape`  — trójwymiarowa powierzchnia parametrów: szeroki płaskowyż (odporny) vs wąski szczyt z flagą
                 „najlepszy backtest” (przeuczenie).
- `graveyard`  — nocny cmentarz strategii: księżyc, wzgórza, nagrobki z wyrytymi krzywymi, mgła; twarz z boku.
- `dashboard`  — szklany dashboard w perspektywie 3D (krzywa IS/OOS, mapa parametrów, histogram, bramki ✓/✗),
                 twarz z poświatą.
- `funnel`     — izometryczna taśma z bramkami walidacji: kostki-pomysły odpadają po drodze, dociera jedna.
- `layers`     — trzy warstwy w 3D: publikacja → kod → wynik z załamaniem.

Grafiki są dekoracyjne: bez osi z wartościami i bez liczb (liczby wyłącznie z Ledgera / kart fabryki).
Słowa w *gwiazdkach* = akcent, `|` = nowa linia.

Wymaga: Pillow, `playwright` (pip) i Chromium. Na VPS: `pip install playwright && playwright install chromium`
(~150 MB na dysku, ~300 MB RAM na czas renderu) albo `--chromium <ścieżka>`. Fonty: assets/fonts.

Przykład:
    python3 scripts/thumbnail_scenes.py --scene montecarlo --text "LUCK|OR *SKILL?*" --out thumb.jpg
"""

from __future__ import annotations

import argparse
import glob
import html
import math
import random
import sys
import tempfile
import zlib
from pathlib import Path

from PIL import Image

import thumbnail as base

W, H = 1280, 720
FONTS = Path("assets/fonts").resolve()


def rgb(c, a=1.0) -> str:
    return f"rgba({c[0]},{c[1]},{c[2]},{a})"


def headline(text: str, accent, size: int, font="Anton", color="#f5f7fa", lh=1.0, extra="") -> str:
    """Nagłówek HTML z akcentem (*słowo*) i liniami (|)."""
    out = []
    for ln in base.parse_lines(text):
        out.append(" ".join(f'<span style="color:{rgb(accent)}">{html.escape(w)}</span>' if hot else html.escape(w)
                            for w, hot in ln))
    return (f'<div class="hl" style="font-family:{font};font-size:{size}px;line-height:{lh};color:{color};'
            f'{extra}">' + "<br>".join(out) + "</div>")


def page(body: str, bg: str) -> str:
    fonts = "".join(f"@font-face{{font-family:'{n}';src:url('{(FONTS / f).as_uri()}')}}" for n, f in [
        ("Anton", "Anton-Regular.ttf"), ("DMSerif", "DMSerifDisplay-Regular.ttf"),
        ("Plex", "IBMPlexMono-Regular.ttf"), ("PlexB", "IBMPlexMono-Bold.ttf")])
    return f"""<!doctype html><html><head><meta charset="utf-8"><style>{fonts}
*{{box-sizing:border-box}} html,body{{margin:0;width:{W}px;height:{H}px;overflow:hidden;background:{bg}}}
.abs{{position:absolute}} .hl{{text-shadow:0 6px 24px rgba(0,0,0,.55),0 3px 0 rgba(0,0,0,.6);letter-spacing:.5px}}
</style></head><body>{body}</body></html>"""


def walk(rnd, n, drift, vol):
    v, out = 0.0, []
    for _ in range(n):
        v += drift + rnd.gauss(0, vol)
        out.append(v)
    return out


def face_html(face: Path | None, accent, workdir: Path, box, glow=True) -> str:
    """Wycięcie twarzy: kadr głowa+barki, dopasowanie do sceny; pozycja box = (left, bottom, max_w, max_h)."""
    if not face:
        return ""
    base.FACE_ZOOM = True
    f = base.load_face(face).convert("RGBA")
    f = base.fit_into(f, box[2], box[3])
    f = base.grade_face(f, accent)
    p = workdir / "face.png"
    f.save(p)
    flt = f"filter:drop-shadow(0 0 28px {rgb(accent, .55)}) drop-shadow(0 18px 30px rgba(0,0,0,.6));" if glow else \
        "filter:drop-shadow(0 18px 30px rgba(0,0,0,.6));"
    return f'<img class="abs" src="{p.as_uri()}" style="left:{box[0]}px;bottom:{box[1]}px;{flt}">'


# --- sceny ---------------------------------------------------------------------


def s_montecarlo(a, accent, rnd, wd) -> str:
    n, steps, x0, x1, y0 = 230, 120, 70, 960, 430
    paths = [walk(rnd, steps, 0.02, 1.0) for _ in range(n)]
    lo = min(min(p) for p in paths)
    hi = max(max(p) for p in paths)
    sy = lambda v: 650 - (v - lo) / (hi - lo) * 520
    finals = sorted(range(n), key=lambda i: paths[i][-1])
    best = finals[-1]
    svg = []
    for rank, i in enumerate(finals):
        if i == best:
            continue
        hue = int(rank / n * 130)
        pts = " ".join(f"{x0 + (x1 - x0) * k / (steps - 1):.1f},{sy(v):.1f}" for k, v in enumerate(paths[i]))
        svg.append(f'<polyline points="{pts}" fill="none" stroke="hsla({hue},80%,60%,.16)" stroke-width="2"/>')
    pts = " ".join(f"{x0 + (x1 - x0) * k / (steps - 1):.1f},{sy(v):.1f}" for k, v in enumerate(paths[best]))
    svg.append(f'<polyline points="{pts}" fill="none" stroke="#ffd166" stroke-width="7" filter="url(#glow)"/>')
    svg.append(f'<polyline points="{pts}" fill="none" stroke="#fff4d6" stroke-width="2.5"/>')
    # histogram wyników po prawej
    bins = [0] * 24
    for p in paths:
        bins[min(23, int((p[-1] - lo) / (hi - lo) * 24))] += 1
    mx = max(bins)
    bh = 520 / 24
    for b, c in enumerate(bins):
        yb = 650 - (b + 1) * bh
        hot = b == min(23, int((paths[best][-1] - lo) / (hi - lo) * 24))
        svg.append(f'<rect x="985" y="{yb + 2:.1f}" width="{c / mx * 230:.1f}" height="{bh - 4:.1f}" rx="3" '
                   f'fill="{"#ffd166" if hot else "rgba(150,170,200,.45)"}"/>')
    ey = sy(paths[best][-1])
    svg.append(f'<line x1="{x1}" y1="{ey}" x2="985" y2="{ey}" stroke="#ffd166" stroke-dasharray="6 6" stroke-width="2"/>')
    svg.append(f'<circle cx="{x1}" cy="{ey}" r="10" fill="#ffd166" filter="url(#glow)"/>')
    body = f"""
<div class="abs" style="inset:0;background:radial-gradient(ellipse at 35% 60%,#16233a 0%,#070b14 70%)"></div>
<svg class="abs" width="{W}" height="{H}"><defs><filter id="glow" x="-50%" y="-50%" width="200%" height="200%">
<feGaussianBlur stdDeviation="6" result="b"/><feMerge><feMergeNode in="b"/><feMergeNode in="SourceGraphic"/></feMerge>
</filter></defs>{''.join(svg)}</svg>
<div class="abs" style="left:{x1 - 210}px;top:{ey - 58}px;font-family:PlexB;font-size:22px;color:#ffd166;
text-shadow:0 2px 8px #000">{html.escape(a.sub or "YOUR BACKTEST")}</div>
<div class="abs" style="left:56px;top:40px">{headline(a.text, accent, 128)}</div>"""
    return page(body, "#070b14")


def s_landscape(a, accent, rnd, wd) -> str:
    N, az, el = 38, math.radians(-38), math.radians(32)
    cx, cy, sx, sz = 720, 500, 430, 235
    px, py = rnd.uniform(0.35, 0.55), rnd.uniform(-0.3, -0.1)

    def z(x, y):
        return (0.28 * math.exp(-((x + 0.45) ** 2 + (y - 0.35) ** 2) / 0.22)
                + 1.0 * math.exp(-((x - px) ** 2 + (y - py) ** 2) / 0.0045)
                + 0.03 * math.sin(4 * x) * math.cos(3 * y))

    def proj(x, y, h):
        X = x * math.cos(az) - y * math.sin(az)
        Y = x * math.sin(az) + y * math.cos(az)
        return cx + X * sx, cy + Y * sx * math.sin(el) - h * sz, Y

    pal = [(18, 34, 70), (24, 92, 128), (40, 160, 150), (120, 210, 140), (250, 214, 92), (240, 90, 60)]

    def col(t):
        t = max(0.0, min(1.0, t)) * (len(pal) - 1)
        i = min(int(t), len(pal) - 2)
        f = t - i
        return tuple(int(pal[i][k] + (pal[i + 1][k] - pal[i][k]) * f) for k in range(3))

    g = [[(-1 + 2 * i / N, -1 + 2 * j / N) for j in range(N + 1)] for i in range(N + 1)]
    quads = []
    for i in range(N):
        for j in range(N):
            corners = [g[i][j], g[i + 1][j], g[i + 1][j + 1], g[i][j + 1]]
            hs = [z(*c) for c in corners]
            pr = [proj(c[0], c[1], h) for c, h in zip(corners, hs)]
            depth = sum(p[2] for p in pr) / 4
            quads.append((depth, pr, sum(hs) / 4))
    quads.sort(key=lambda q: q[0])
    svg = []
    for _, pr, h in quads:
        c = col(h / 0.75)
        pts = " ".join(f"{p[0]:.1f},{p[1]:.1f}" for p in pr)
        svg.append(f'<polygon points="{pts}" fill="{rgb(c)}" stroke="rgba(255,255,255,.18)" stroke-width="0.8"/>')
    tx, ty, _ = proj(px, py, z(px, py))
    svg.append(f'<line x1="{tx}" y1="{ty}" x2="{tx}" y2="{ty - 120}" stroke="#fff" stroke-width="5"/>')
    svg.append(f'<polygon points="{tx},{ty - 120} {tx + 80},{ty - 100} {tx},{ty - 80}" fill="{rgb(accent)}"/>')
    rx, ry, _ = proj(-0.45, 0.35, z(-0.45, 0.35))
    body = f"""
<div class="abs" style="inset:0;background:radial-gradient(ellipse at 60% 40%,#1b2a44 0%,#080c16 75%)"></div>
<svg class="abs" width="{W}" height="{H}">{''.join(svg)}</svg>
<div class="abs" style="left:{tx + 12}px;top:{ty - 178}px;font-family:PlexB;font-size:22px;color:#fff;
background:{rgb(accent, .9)};padding:4px 10px;border-radius:6px">{html.escape(a.sub or "BEST BACKTEST")}</div>
<div class="abs" style="left:{rx - 70}px;top:{ry - 70}px;font-family:PlexB;font-size:22px;color:#08130c;
background:rgba(120,231,150,.92);padding:4px 10px;border-radius:6px">ROBUST</div>
<div class="abs" style="left:56px;top:40px">{headline(a.text, accent, 120)}</div>"""
    return page(body, "#080c16")


def s_graveyard(a, accent, rnd, wd) -> str:
    stars = "".join(f'<circle cx="{rnd.uniform(0, W):.0f}" cy="{rnd.uniform(0, 380):.0f}" r="{rnd.uniform(.6, 2.2):.1f}" '
                    f'fill="rgba(255,255,255,{rnd.uniform(.3, .9):.2f})"/>' for _ in range(140))

    def hill(base_y, amp, seed, color):
        r = random.Random(seed)
        ph = [r.uniform(0, 6) for _ in range(3)]
        pts = [f"{x},{base_y - amp * (math.sin(x / 210 + ph[0]) + .5 * math.sin(x / 90 + ph[1]) + .3 * math.sin(x / 47 + ph[2])):.1f}"
               for x in range(0, W + 21, 20)]
        return f'<polygon points="0,{H} {" ".join(pts)} {W},{H}" fill="{color}"/>'

    hills = hill(470, 34, 1, "#231a3d") + hill(540, 26, 2, "#17122b") + hill(610, 18, 3, "#0d0a19")
    stones = []
    for k, (x, y, w, h, rot) in enumerate([(120, 600, 150, 200, -6), (330, 640, 120, 160, 4), (520, 600, 170, 230, -2),
                                            (720, 660, 110, 140, 7)]):
        ys = walk(rnd, 40, 0.6, 1.0)
        cut = 26
        ys = ys[:cut] + [ys[cut - 1] - (i + 1) * 1.8 + rnd.gauss(0, .8) for i in range(40 - cut)]
        lo, hi = min(ys), max(ys)
        curve = " ".join(f"{-w / 2 + 18 + (w - 36) * i / 39:.1f},{-h * .42 - (v - lo) / (hi - lo or 1) * h * .3:.1f}"
                         for i, v in enumerate(ys))
        stones.append(f"""<g transform="translate({x},{y}) rotate({rot})">
<path d="M{-w / 2},0 L{-w / 2},{-h + w / 2} A{w / 2},{w / 2} 0 0 1 {w / 2},{-h + w / 2} L{w / 2},0 Z"
 fill="url(#stone)" stroke="#2c2f38" stroke-width="3"/>
<text x="0" y="{-h + w / 2 + 6}" text-anchor="middle" font-family="DMSerif" font-size="{w * .22:.0f}" fill="#3a3e48">R.I.P.</text>
<polyline points="{curve}" fill="none" stroke="#3a3e48" stroke-width="4"/>
<polyline points="{curve}" fill="none" stroke="rgba(255,255,255,.25)" stroke-width="1.5" transform="translate(1,1)"/>
</g>""")
    fh = face_html(a.face, accent, wd, (W - 470, 0, 470, 560), glow=False)
    body = f"""
<div class="abs" style="inset:0;background:linear-gradient(#060918 0%,#1b1438 55%,#3d2650 100%)"></div>
<svg class="abs" width="{W}" height="{H}"><defs>
<radialGradient id="halo"><stop offset="0" stop-color="rgba(255,248,220,.55)"/><stop offset="1" stop-color="rgba(255,248,220,0)"/></radialGradient>
<linearGradient id="stone" x1="0" x2="1"><stop offset="0" stop-color="#9aa0ad"/><stop offset="1" stop-color="#5f6573"/></linearGradient>
</defs>{stars}<circle cx="1010" cy="150" r="190" fill="url(#halo)"/><circle cx="1010" cy="150" r="72" fill="#f4efd9"/>
<circle cx="985" cy="135" r="12" fill="rgba(0,0,0,.06)"/><circle cx="1032" cy="172" r="8" fill="rgba(0,0,0,.06)"/>
{hills}{''.join(stones)}</svg>
{fh}
<div class="abs" style="left:0;right:0;bottom:0;height:300px;background:linear-gradient(rgba(190,190,220,0),rgba(200,200,230,.6) 70%,rgba(210,210,235,.7));
filter:blur(6px)"></div>
<div class="abs" style="left:56px;top:36px">{headline(a.text, accent, 116)}</div>"""
    return page(body, "#060918")


def s_dashboard(a, accent, rnd, wd) -> str:
    ys = walk(rnd, 110, 0.0, 1.0)
    cut = 66
    ys = [v + i * 0.55 if i < cut else v + cut * 0.55 - (i - cut) * 0.9 for i, v in enumerate(ys)]
    lo, hi = min(ys), max(ys)
    pts = " ".join(f"{10 + 500 * i / 109:.1f},{190 - (v - lo) / (hi - lo) * 165:.1f}" for i, v in enumerate(ys))
    sx = 10 + 500 * cut / 109
    eq = f"""<svg width="520" height="200"><polyline points="{pts}" fill="none" stroke="{rgb(accent)}" stroke-width="5"/>
<line x1="{sx}" y1="0" x2="{sx}" y2="200" stroke="rgba(255,255,255,.6)" stroke-dasharray="6 6" stroke-width="2"/>
<text x="{sx - 10}" y="18" text-anchor="end" font-family="PlexB" font-size="14" fill="rgba(255,255,255,.7)">IN-SAMPLE</text>
<text x="{sx + 10}" y="18" font-family="PlexB" font-size="14" fill="rgba(255,255,255,.7)">OUT-OF-SAMPLE</text></svg>"""
    hot = (rnd.randint(1, 6), rnd.randint(1, 6))
    cells = ""
    for r in range(8):
        for c in range(8):
            d = math.hypot(r - hot[0], c - hot[1])
            t = max(0.0, 1 - d / 2.2) if (r, c) != hot else 1.0
            col = (int(30 + 210 * t), int(60 + 60 * (1 - t)), int(110 - 60 * t))
            ring = f"outline:3px solid #fff;outline-offset:-3px;" if (r, c) == hot else ""
            cells += f'<div style="background:{rgb(col)};border-radius:4px;{ring}"></div>'
    heat = f'<div style="display:grid;grid-template-columns:repeat(8,1fr);gap:4px;width:200px;height:200px">{cells}</div>'
    bars = "".join(f'<rect x="{6 + i * 17}" y="{150 - h:.0f}" width="13" height="{h:.0f}" rx="2" fill="rgba(140,180,255,.7)"/>'
                   for i, h in enumerate(140 * math.exp(-((i - 7) / 3.6) ** 2) + rnd.uniform(0, 12) for i in range(15)))
    hist = f'<svg width="260" height="155">{bars}</svg>'
    gates = "".join(f'<div style="display:flex;justify-content:space-between;align-items:center;margin:9px 0">'
                    f'<span>{g}</span><span style="background:{bg};color:#08130c;border-radius:6px;padding:1px 10px;'
                    f'font-family:PlexB">{m}</span></div>'
                    for g, m, bg in [("In-sample", "✓", "#7be3a0"), ("Out-of-sample", "✗", rgb(accent)),
                                     ("Costs +50%", "✗", rgb(accent)), ("Walk-forward", "✗", rgb(accent))])
    glass = ("background:rgba(255,255,255,.07);border:1px solid rgba(255,255,255,.22);border-radius:18px;"
             "box-shadow:0 30px 60px rgba(0,0,0,.45),inset 0 1px 0 rgba(255,255,255,.2);padding:16px;"
             "color:rgba(255,255,255,.85);font-family:Plex;font-size:18px")
    cap = lambda t: f'<div style="font-family:PlexB;font-size:15px;letter-spacing:2px;opacity:.7;margin-bottom:8px">{t}</div>'
    bokeh = "".join(f'<div class="abs" style="left:{rnd.uniform(0, W):.0f}px;top:{rnd.uniform(0, H):.0f}px;'
                    f'width:{s:.0f}px;height:{s:.0f}px;border-radius:50%;background:{rgb(accent if rnd.random() < .4 else (90, 140, 255), .12)};'
                    f'filter:blur(6px)"></div>' for s in [rnd.uniform(20, 90) for _ in range(18)])
    fh = face_html(a.face, accent, wd, (W - 440, 0, 440, 600))
    body = f"""
<div class="abs" style="inset:0;background:radial-gradient(ellipse at 30% 70%,{rgb(accent, .25)} 0%,rgba(0,0,0,0) 55%),
radial-gradient(ellipse at 80% 20%,rgba(70,110,255,.25) 0%,rgba(0,0,0,0) 50%),#070a14"></div>{bokeh}
<div class="abs" style="left:40px;top:150px;perspective:1500px">
 <div style="transform:rotateY(24deg) rotateX(10deg) rotateZ(-2deg);transform-origin:left center;
  display:grid;grid-template-columns:560px 240px;grid-template-rows:250px 250px;gap:18px">
  <div style="{glass}">{cap("EQUITY")}{eq}</div>
  <div style="{glass}">{cap("PARAMETERS")}{heat}</div>
  <div style="{glass}">{cap("VALIDATION GATES")}{gates}</div>
  <div style="{glass}">{cap("RETURNS")}{hist}</div>
 </div></div>
{fh}
<div class="abs" style="left:52px;top:26px">{headline(a.text, accent, 118)}</div>"""
    return page(body, "#070a14")


def s_funnel(a, accent, rnd, wd) -> str:
    s, cx, cy = 46, 300, 250

    def iso(x, y, z):
        return cx + (x - y) * s * 0.866, cy + (x + y) * s * 0.5 - z * s

    seen: list[tuple[float, float]] = []

    def poly(pts, fill, stroke="rgba(0,0,0,.35)"):
        seen.extend(pts)
        return f'<polygon points="{" ".join(f"{p[0]:.1f},{p[1]:.1f}" for p in pts)}" fill="{fill}" stroke="{stroke}" stroke-width="1.5"/>'

    def shade(c, f):
        return rgb(tuple(min(255, int(v * f)) for v in c))

    def cube(x, y, z, d, c, glow=False):
        top = [iso(x, y, z + d), iso(x + d, y, z + d), iso(x + d, y + d, z + d), iso(x, y + d, z + d)]
        left = [iso(x, y + d, z), iso(x + d, y + d, z), iso(x + d, y + d, z + d), iso(x, y + d, z + d)]
        right = [iso(x + d, y, z), iso(x + d, y + d, z), iso(x + d, y + d, z + d), iso(x + d, y, z + d)]
        g = ' filter="url(#glow)"' if glow else ""
        return f"<g{g}>" + poly(top, shade(c, 1.15)) + poly(left, shade(c, .8)) + poly(right, shade(c, .6)) + "</g>"

    items = []
    belt_len = 15
    # taśma
    belt = (poly([iso(0, 0, 0), iso(belt_len, 0, 0), iso(belt_len, 2, 0), iso(0, 2, 0)], "#2a3346") +
            poly([iso(0, 2, 0), iso(belt_len, 2, 0), iso(belt_len, 2, -.5), iso(0, 2, -.5)], "#1a2030") +
            poly([iso(belt_len, 0, 0), iso(belt_len, 2, 0), iso(belt_len, 2, -.5), iso(belt_len, 0, -.5)], "#141926"))
    for k in range(0, belt_len * 2):
        x = k * .5
        a1, a2 = iso(x, 0, 0), iso(x, 2, 0)
        belt += f'<line x1="{a1[0]:.1f}" y1="{a1[1]:.1f}" x2="{a2[0]:.1f}" y2="{a2[1]:.1f}" stroke="rgba(255,255,255,.06)"/>'
    gates = [(4, a.sub.split(",")[0] if a.sub else "COSTS"), (8, "OUT-OF-SAMPLE"), (12, "WALK-FORWARD")]
    labels = []
    for gx, name in gates:
        for y in (-.3, 2):
            items.append((gx + y, 0, cube(gx, y, 0, .3, (90, 100, 130)) + cube(gx, y, .3, .3, (90, 100, 130)) +
                          cube(gx, y, .6, .3, (90, 100, 130)) + cube(gx, y, .9, .3, (90, 100, 130))))
        bar = [iso(gx, -.3, 1.2), iso(gx + .3, -.3, 1.2), iso(gx + .3, 2.3, 1.2), iso(gx, 2.3, 1.2)]
        items.append((gx + 2.5, 1, poly(bar, rgb(accent), rgb(accent)) +
                      f'<polyline points="{" ".join(f"{p[0]:.1f},{p[1]:.1f}" for p in bar[:3])}" fill="none" '
                      f'stroke="{rgb(accent)}" stroke-width="4" filter="url(#glow)"/>'))
        lx, ly = iso(gx, -.3, 1.6)
        labels.append(f'<text x="{lx - 20:.0f}" y="{ly:.0f}" font-family="PlexB" font-size="17" fill="rgba(255,255,255,.85)" '
                      f'transform="rotate(-30 {lx:.0f} {ly:.0f})">{html.escape(name)}</text>')
    counts = [(0.4, 3.6, 9), (4.5, 7.6, 5), (8.5, 11.6, 3)]
    for x0, x1, n in counts:
        for k in range(n):
            x = x0 + (x1 - x0) * (k % 4) / 4 + rnd.uniform(0, .2)
            y = .15 + (k // 4) * .6 + rnd.uniform(0, .2)
            items.append((x + y, 0.5, cube(x, y, 0, .5, (110, 140, 200))))
    items.append((13.6, 0.5, cube(13.3, .7, 0, .6, (110, 231, 140), glow=True)))
    for k in range(7):  # odrzucone — spadają przed taśmą
        x = rnd.uniform(3.5, 13)
        items.append((x + 3, 2, cube(x, rnd.uniform(2.6, 3.4), -rnd.uniform(0.8, 2.2), .42, (210, 70, 60))))
    items.sort(key=lambda t: (t[0], t[1]))
    svg = belt + "".join(i[2] for i in items) + "".join(labels)
    # cała scena wpasowana w ramkę pod nagłówkiem (x 70–1230, y 200–700)
    bx0, by0 = min(p[0] for p in seen), min(p[1] for p in seen)
    bx1, by1 = max(p[0] for p in seen), max(p[1] for p in seen)
    k = min(1160 / (bx1 - bx0), 500 / (by1 - by0))
    tx, ty = 70 + (1160 - (bx1 - bx0) * k) / 2 - bx0 * k, 200 - by0 * k
    body = f"""
<div class="abs" style="inset:0;background:radial-gradient(ellipse at 55% 55%,#1a2238 0%,#06080f 72%)"></div>
<svg class="abs" width="{W}" height="{H}"><defs><filter id="glow" x="-50%" y="-50%" width="200%" height="200%">
<feGaussianBlur stdDeviation="5" result="b"/><feMerge><feMergeNode in="b"/><feMergeNode in="SourceGraphic"/></feMerge>
</filter></defs><g transform="translate({tx:.1f},{ty:.1f}) scale({k:.3f})">{svg}</g></svg>
<div class="abs" style="left:56px;top:34px">{headline(a.text, accent, 112)}</div>"""
    return page(body, "#06080f")


def s_layers(a, accent, rnd, wd) -> str:
    lines = "".join(f'<div style="height:9px;margin:9px 0;width:{rnd.uniform(70, 100):.0f}%;background:#c9c9c9;border-radius:3px"></div>'
                    for _ in range(9))
    paper = (f'<div style="font-family:DMSerif;font-size:30px;color:#222">{html.escape(a.sub or "Working Paper")}</div>'
             f'<div style="height:10px"></div>{lines[:len(lines) // 2]}'
             f'<div style="height:12px;margin:10px 0;width:92%;background:#ffd84d;border-radius:3px"></div>{lines[len(lines) // 2:]}')
    toks = [("def", "#c792ea"), ("signal", "#82aaff"), ("(data):", "#d6deeb"), ("if", "#c792ea"), ("cond", "#addb67"),
            ("return", "#c792ea"), ("entry", "#f78c6c"), ("exit", "#f78c6c"), ("costs", "#7fdbca"), ("...", "#637777")]
    code = ""
    for ln in range(9):
        ind = 0 if ln in (0, 5) else 28
        code += f'<div style="margin:5px 0 5px {ind}px;font-family:Plex;font-size:19px">' + " ".join(
            f'<span style="color:{c}">{t}</span>' for t, c in rnd.sample(toks, 3)) + "</div>"
    ys = walk(rnd, 70, 0.0, 1.0)
    ys = [v + i * .6 if i < 42 else v + 42 * .6 - (i - 42) * 1.3 for i, v in enumerate(ys)]
    lo, hi = min(ys), max(ys)
    pts = " ".join(f"{10 + 480 * i / 69:.1f},{290 - (v - lo) / (hi - lo) * 250:.1f}" for i, v in enumerate(ys))
    chart = (f'<svg width="500" height="300"><polyline points="{pts}" fill="none" stroke="{rgb(accent)}" stroke-width="7"/></svg>'
             f'<div class="abs" style="right:18px;top:14px;width:64px;height:64px;border-radius:50%;background:{rgb(accent)};'
             f'color:#fff;font:700 44px/64px Plex;text-align:center;border:4px solid #fff">✗</div>')
    tag = lambda t, c: (f'<div style="position:absolute;left:0;top:-50px;font-family:PlexB;font-size:26px;color:{c};'
                        f'letter-spacing:3px">{t}</div>')
    tilt = "transform:perspective(1800px) rotateX(52deg) rotateZ(-36deg);transform-origin:center"
    card = (f"position:absolute;left:70px;width:560px;height:360px;border-radius:16px;padding:22px;"
            f"box-shadow:0 50px 70px rgba(0,0,0,.6);{tilt}")
    body = f"""
<div class="abs" style="inset:0;background:linear-gradient(135deg,#0b1222 0%,#141d33 50%,#0a0f1c 100%)"></div>
<div style="{card};top:310px;background:#fbfaf6">{tag("PAPER", "#ffffff")}{paper}</div>
<div style="{card};top:190px;background:#0f1724;border:1px solid #2a3a55">{tag("CODE", "#82aaff")}{code}</div>
<div style="{card};top:50px;background:rgb(22,12,16);border:3px solid {rgb(accent)}">{tag("REALITY", rgb(accent))}
 <div style="position:relative">{chart}</div></div>
<div class="abs" style="right:56px;top:300px;text-align:right">{headline(a.text, accent, 124)}</div>"""
    return page(body, "#0b1222")


SCENES = {"montecarlo": s_montecarlo, "landscape": s_landscape, "graveyard": s_graveyard,
          "dashboard": s_dashboard, "funnel": s_funnel, "layers": s_layers}


def chromium_path(arg: str | None) -> str | None:
    if arg:
        return arg
    found = sorted(glob.glob("/opt/pw-browsers/chromium-*/chrome-linux*/chrome"))
    return found[-1] if found else None   # None = Chromium zainstalowany przez `playwright install`


def main() -> int:
    global FONTS
    ap = argparse.ArgumentParser()
    ap.add_argument("--scene", required=True, choices=SCENES)
    ap.add_argument("--text", required=True, help="2–4 słowa; *słowo* = akcent, | = nowa linia")
    ap.add_argument("--sub", default="", help="podpis pomocniczy (etykieta ścieżki/szczytu, tytuł publikacji)")
    ap.add_argument("--verdict", choices=base.ACCENTS, default="fail")
    ap.add_argument("--face", type=Path)
    ap.add_argument("--fonts", type=Path, default=FONTS)
    ap.add_argument("--chromium", help="ścieżka do Chromium (domyślnie z Playwright)")
    ap.add_argument("--keep-html", action="store_true", help="zapisz HTML obok JPG (do ręcznych poprawek)")
    ap.add_argument("--out", required=True, type=Path)
    a = ap.parse_args()
    FONTS = a.fonts.resolve()
    accent = {"fail": (240, 72, 60), "pass": (110, 231, 140), "neutral": (255, 196, 61)}[a.verdict]
    rnd = random.Random(zlib.crc32((a.scene + a.text).encode()))

    from playwright.sync_api import sync_playwright

    with tempfile.TemporaryDirectory() as tmp:
        wd = Path(tmp)
        doc = SCENES[a.scene](a, accent, rnd, wd)
        src = wd / "scene.html"
        src.write_text(doc, encoding="utf-8")
        if a.keep_html:
            a.out.with_suffix(".html").write_text(doc, encoding="utf-8")
        png = wd / "scene.png"
        with sync_playwright() as p:
            browser = p.chromium.launch(executable_path=chromium_path(a.chromium))
            pg = browser.new_page(viewport={"width": W, "height": H})
            pg.goto(src.as_uri())
            pg.wait_for_timeout(150)
            pg.screenshot(path=str(png))
            browser.close()
        base.save_jpg(Image.open(png).convert("RGB"), a.out)
    print(a.out)
    return 0


if __name__ == "__main__":
    sys.exit(main())
