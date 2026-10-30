#!/usr/bin/env python3
"""Kontrola jakości miniatur (docs/YT_PUBLISHING_STANDARD.md §3) — raport PASS/WARN/FAIL dla każdego wariantu.

Kryteria (każde 0–10, ocena końcowa = NAJSŁABSZE kryterium, nie średnia):
- `format`    — 1280×720, ≤ 2 MB,
- `ocr_small` — czy Tesseract odczyta słowa z wersji 168×94 (rozmiar z listy w telefonie); jeśli maszyna
                nie odczyta, człowiek też będzie miał problem,
- `contrast`  — kontrast WCAG liter vs tło pod nimi (z ramek słów OCR w pełnym rozmiarze), cel ≥ 4,5:1,
- `timestamp` — prawy dolny róg wolny od tekstu i mocnych elementów (YouTube zasłania go czasem trwania),
- `attention` — mapa uwagi (OpenCV, spectral residual): ile „uwagi” przypada na strefę tekstu i strefę twarzy
                vs reszta kadru; zapisuje też mapę cieplną `<plik>-uwaga.png`,
- `rules`     — 2–4 słowa, zakazane słowa z CLAUDE.md, brak kwot.

Wymaga: Pillow, opencv-contrib-python-headless, pytesseract, systemowego `tesseract-ocr`.
Uruchamiać interpreterem z venv, np.:
    ~/.venvs/thumbs/bin/python scripts/thumbnail_check.py --text "WHY NOT|*100%* STOCKS?" content/publish/<slug>/thumbnail-*.jpg
`--text` w składni thumbnail.py (`*akcent*`, `|`) — oczekiwane słowa do porównania z OCR.
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

import cv2
import numpy as np
import pytesseract
from PIL import Image, ImageOps

W, H = 1280, 720
MAX_BYTES = 2 * 1024 * 1024
# Prawy dolny róg zasłaniany przez znacznik czasu (z zapasem: na telefonie badge jest względnie większy).
TS_BOX = (int(W * 0.80), int(H * 0.84), W, H)
FORBIDDEN = ["only", "secret", "ai", "ai-powered", "100%", "holy grail", "guaranteed"]


def words_of(text: str) -> list[str]:
    return [w for w in re.findall(r"[^\s|*]+", text)]


def norm(w: str) -> str:
    return re.sub(r"[^a-z0-9%]", "", w.lower())


def ocr_words(img: Image.Image, scales=(1.0,), expected: list[str] | None = None) -> list[dict]:
    """Słowa z OCR z ramkami we współrzędnych obrazu wejściowego. Próbuje kilku skal (Tesseract gubi bardzo
    duże i bardzo wąskie litery) oraz wersji zwykłej i odwróconej; wybiera wynik z największą liczbą trafień."""
    best: list[dict] = []
    gray0 = ImageOps.grayscale(img)

    def quality(found):
        return match_ratio(expected, found) if expected else len(found)

    for sc in scales:
        gray = gray0.resize((int(gray0.width * sc), int(gray0.height * sc)), Image.LANCZOS) if sc != 1 else gray0
        for variant in (gray, ImageOps.invert(gray)):
            data = pytesseract.image_to_data(variant, config="--psm 11", output_type=pytesseract.Output.DICT)
            found = []
            for i, t in enumerate(data["text"]):
                if t.strip() and float(data["conf"][i]) > 40:
                    found.append({"text": t, "conf": float(data["conf"][i]),
                                  "box": tuple(int(v / sc) for v in (data["left"][i], data["top"][i],
                                                                      data["left"][i] + data["width"][i],
                                                                      data["top"][i] + data["height"][i]))})
            if quality(found) > quality(best):
                best = found
    return best


def match_ratio(expected: list[str], found: list[dict]) -> float:
    got = {norm(f["text"]) for f in found}
    exp = [norm(w) for w in expected if norm(w)]
    return sum(1 for w in exp if w in got) / len(exp) if exp else 0.0


def rel_lum(rgb: np.ndarray) -> np.ndarray:
    c = rgb / 255.0
    c = np.where(c <= 0.03928, c / 12.92, ((c + 0.055) / 1.055) ** 2.4)
    return 0.2126 * c[..., 0] + 0.7152 * c[..., 1] + 0.0722 * c[..., 2]


def box_contrast(arr: np.ndarray, box) -> float:
    """Kontrast WCAG w ramce słowa: piksele dzielone progiem Otsu na litery i tło, mediany luminancji."""
    x0, y0, x1, y1 = box
    crop = arr[y0:y1, x0:x1]
    if crop.size == 0:
        return 0.0
    gray = cv2.cvtColor(crop, cv2.COLOR_RGB2GRAY)
    _, mask = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
    lum = rel_lum(crop.astype(float))
    a, b = lum[mask > 0], lum[mask == 0]
    if a.size < 10 or b.size < 10:
        return 0.0
    hi, lo = max(np.median(a), np.median(b)), min(np.median(a), np.median(b))
    return (hi + 0.05) / (lo + 0.05)


def overlap(a, b) -> bool:
    return not (a[2] <= b[0] or b[2] <= a[0] or a[3] <= b[1] or b[3] <= a[1])


def attention_map(arr: np.ndarray) -> np.ndarray:
    sal = cv2.saliency.StaticSaliencySpectralResidual_create()
    ok, m = sal.computeSaliency(cv2.cvtColor(arr, cv2.COLOR_RGB2BGR))
    m = cv2.GaussianBlur(m.astype(np.float32), (0, 0), 12)
    return m / (m.sum() or 1)


def score_band(value: float, bad: float, good: float) -> int:
    """Liniowo 0 (≤ bad) … 10 (≥ good)."""
    if good == bad:
        return 10
    return int(round(max(0.0, min(1.0, (value - bad) / (good - bad))) * 10))


def check(path: Path, expected: list[str], heatmap: bool) -> dict:
    img = Image.open(path).convert("RGB")
    arr = np.asarray(img)
    res: dict[str, tuple[int, str]] = {}

    size = path.stat().st_size
    ok = img.size == (W, H) and size <= MAX_BYTES
    res["format"] = (10 if ok else 0, f"{img.width}×{img.height}, {size // 1024} KB")

    full = ocr_words(img, (1.0, 0.5), expected)
    small = img.resize((168, 94), Image.LANCZOS)
    # 168×94 powiększone z powrotem — OCR „widzi” tylko informację, która przetrwała zmniejszenie.
    small_found = ocr_words(small.resize((672, 376), Image.BICUBIC), (1.0,), expected)
    if expected:
        r_full, r_small = match_ratio(expected, full), match_ratio(expected, small_found)
        res["ocr_small"] = (score_band(r_small, 0.25, 1.0),
                            f"168×94: {r_small:.0%} słów odczytanych (pełny rozmiar: {r_full:.0%})")
    else:
        res["ocr_small"] = (10 if small_found else 0, "168×94: " + " ".join(f["text"] for f in small_found))

    exp_n = {norm(w) for w in expected}
    text_boxes = [f["box"] for f in full if not expected or norm(f["text"]) in exp_n]
    contrasts = [box_contrast(arr, b) for b in text_boxes]
    if contrasts:
        worst = min(contrasts)
        res["contrast"] = (score_band(worst, 3.0, 4.5), f"najsłabsze słowo {worst:.1f}:1 (cel ≥ 4,5:1)")
    else:
        res["contrast"] = (0, "brak odczytanych słów — nie da się zmierzyć")

    att = attention_map(arr)
    x0, y0, x1, y1 = TS_BOX
    ts_share = float(att[y0:y1, x0:x1].sum())
    ts_area = (x1 - x0) * (y1 - y0) / (W * H)
    ts_text = [b for b in (f["box"] for f in full) if overlap(b, TS_BOX)]
    ts_score = 0 if ts_text else score_band(-ts_share / ts_area, -3.0, -1.2)
    res["timestamp"] = (ts_score, ("TEKST w strefie czasu: " + ", ".join(f["text"] for f in full
                                                                          if overlap(f["box"], TS_BOX)))
                        if ts_text else f"uwaga w rogu {ts_share:.1%} przy {ts_area:.1%} powierzchni")

    if text_boxes:
        tx0 = min(b[0] for b in text_boxes); ty0 = min(b[1] for b in text_boxes)
        tx1 = max(b[2] for b in text_boxes); ty1 = max(b[3] for b in text_boxes)
        text_share = float(att[ty0:ty1, tx0:tx1].sum())
        text_area = (tx1 - tx0) * (ty1 - ty0) / (W * H)
        lift = text_share / text_area if text_area else 0
        res["attention"] = (score_band(lift, 0.8, 1.5),
                            f"tekst: {text_share:.0%} uwagi na {text_area:.0%} kadru (×{lift:.1f})")
    else:
        res["attention"] = (0, "brak tekstu do oceny")

    words = expected or [f["text"] for f in full]
    joined = " " + " ".join(w.lower() for w in words) + " "
    hits = [f for f in FORBIDDEN if re.search(rf"(?<![a-z0-9]){re.escape(f)}(?![a-z0-9])", joined)]
    money = re.search(r"[$€£]\s*\d|\d\s*(usd|eur|pln|zł|k\$)", joined)
    problems = []
    if not 2 <= len(words) <= 4:
        problems.append(f"{len(words)} słów (standard 2–4)")
    if hits:
        problems.append("zakazane: " + ", ".join(hits))
    if money:
        problems.append("kwota")
    res["rules"] = (10 if not problems else (5 if problems == [f"{len(words)} słów (standard 2–4)"] else 0),
                    "; ".join(problems) or "OK")

    if heatmap:
        hm = (att / att.max() * 255).astype(np.uint8)
        hm = cv2.applyColorMap(hm, cv2.COLORMAP_JET)[..., ::-1]
        over = (0.55 * arr + 0.45 * hm).astype(np.uint8)
        cv2.rectangle(over, TS_BOX[:2], (TS_BOX[2] - 2, TS_BOX[3] - 2), (255, 255, 255), 3)
        Image.fromarray(over).save(path.with_name(path.stem + "-uwaga.png"))
    return res


def verdict(score: int) -> str:
    return "PASS" if score >= 8 else "WARN" if score >= 5 else "FAIL"


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--text", default="", help="oczekiwany tekst miniatury (składnia thumbnail.py)")
    ap.add_argument("--no-heatmap", action="store_true")
    ap.add_argument("images", nargs="+", type=Path)
    a = ap.parse_args()

    expected = words_of(a.text)
    worst_all = 10
    for path in a.images:
        res = check(path, expected, not a.no_heatmap)
        worst = min(s for s, _ in res.values())
        weakest = min(res, key=lambda k: res[k][0])
        worst_all = min(worst_all, worst)
        print(f"\n{path.name}: {verdict(worst)} {worst}/10" + (f" (najsłabsze: {weakest})" if worst < 10 else ""))
        for k, (s, note) in res.items():
            print(f"  {verdict(s):4} {s:2}/10  {k:<10} {note}")
    return 0 if worst_all >= 5 else 1


if __name__ == "__main__":
    sys.exit(main())
