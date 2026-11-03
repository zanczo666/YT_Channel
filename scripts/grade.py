#!/usr/bin/env python3
"""C6 — korekcja barwna: LUT `.cube` + FFmpeg `lut3d`, z klatkami przed/po do zatwierdzenia.

„Kinowy” czy „pastelowy” to kwestia gustu, nie matematyki, więc ten krok ma dwa etapy:

1. `--podglad` zapisuje `kolor-podglad.jpg` (oryginał obok wariantów, trzy momenty filmu) i niczego nie renderuje,
2. dopiero wskazanie `--styl` albo `--lut` renderuje film. Bez wyboru render kończy się błędem — domyślny styl
   oznaczałby korekcję, której nikt nie obejrzał.

LUT-y powstają tu z parametrów (`STYLE`), więc nie zależymy od cudzych plików i ich licencji.

    python3 scripts/grade.py --work /tmp/film-01 --podglad
    python3 scripts/grade.py --work /tmp/film-01 --styl czysty
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import proc  # noqa: E402  — wspólny limiter pamięci

ROZMIAR_LUT = 33
MOMENTY = (0.2, 0.5, 0.8)     # ułamki długości filmu; krańce to często wejście i wyjście z kadru
SZEROKOSC_PODGLADU = 640
FONT = Path("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf")

# Wszystkie wartości są celowo małe: to gadająca głowa, a skóra pierwsza zdradza przesadzoną korekcję.
# wzmocnienie = mnożniki R, G, B; cienie/swiatla = przesunięcie barwy R, G, B rosnące ku czerni/bieli.
STYLE = {
    "czysty": {"wzmocnienie": (0.99, 1.0, 1.05), "kontrast": 0.18, "nasycenie": 1.08, "czern": 0.0,
               "cienie": (0.0, 0.0, 0.0), "swiatla": (0.0, 0.0, 0.0)},
    "kinowy": {"wzmocnienie": (1.0, 1.0, 1.03), "kontrast": 0.28, "nasycenie": 1.02, "czern": 0.0,
               "cienie": (-0.012, 0.004, 0.018), "swiatla": (0.012, 0.004, -0.008)},
    "pastelowy": {"wzmocnienie": (1.0, 1.0, 1.04), "kontrast": 0.0, "nasycenie": 0.90, "czern": 0.035,
                  "cienie": (0.0, 0.004, 0.008), "swiatla": (0.006, 0.003, 0.0)},
}
TRANSFERY_HDR = {"smpte2084", "arib-std-b67"}  # HDR: LUT dla bt709 dałby wyblakły obraz


def ogranicz(x: float) -> float:
    return min(1.0, max(0.0, x))


def krzywa_s(x: float, sila: float) -> float:
    """Kontrast przez krzywą S: środek zostaje na miejscu, więc jasność twarzy prawie się nie zmienia."""
    return x + sila * (x * x * (3 - 2 * x) - x)


def przetworz(r: float, g: float, b: float, st: dict) -> tuple[float, float, float]:
    """Jeden punkt siatki LUT-a. Kolejność: balans bieli, kontrast, nasycenie, tonowanie, poziom czerni."""
    wr, wg, wb = st["wzmocnienie"]
    kanaly = [krzywa_s(ogranicz(c * w), st["kontrast"]) for c, w in ((r, wr), (g, wg), (b, wb))]
    luma = 0.2126 * kanaly[0] + 0.7152 * kanaly[1] + 0.0722 * kanaly[2]   # współczynniki bt709
    wynik = []
    for c, cien, swiatlo in zip(kanaly, st["cienie"], st["swiatla"]):
        c = luma + (c - luma) * st["nasycenie"]
        c += cien * (1 - luma) ** 2 + swiatlo * luma ** 2
        wynik.append(ogranicz(st["czern"] + c * (1 - st["czern"])))
    return wynik[0], wynik[1], wynik[2]


def zapisz_cube(st: dict, cel: Path, rozmiar: int = ROZMIAR_LUT) -> None:
    """Format Adobe `.cube`: czerwony zmienia się najszybciej, niebieski najwolniej."""
    linie = [f'TITLE "{cel.stem}"', f"LUT_3D_SIZE {rozmiar}"]
    n = rozmiar - 1
    for b in range(rozmiar):
        for g in range(rozmiar):
            for r in range(rozmiar):
                linie.append("%.6f %.6f %.6f" % przetworz(r / n, g / n, b / n, st))
    cel.write_text("\n".join(linie) + "\n", encoding="ascii")


def filtr_lut(lut: Path) -> str:
    """Macierz bt709 podana wprost: automatyczna konwersja przy nieoznaczonym pliku wzięłaby bt601
    i LUT dostałby przesunięte barwy. `accurate_rnd` jest konieczne: bez niego sama droga YUV → RGB → YUV
    przyciemniała obraz o ~1,2 poziomu, nawet z LUT-em, który nic nie zmienia (pomiar 2026-11-03)."""
    sciezka = str(lut.resolve()).replace("\\", "\\\\").replace("'", "\\'").replace(":", "\\:")
    konwersja = ("scale=in_color_matrix=bt709:out_color_matrix=bt709:"
                 "flags=bicubic+accurate_rnd+full_chroma_int+full_chroma_inp")
    return f"{konwersja},format=rgb24,lut3d=file='{sciezka}',{konwersja},format=yuv420p"


def zbadaj(film: Path) -> tuple[float, str]:
    """Długość i krzywa przenoszenia (do wykrycia HDR)."""
    res = subprocess.run(["ffprobe", "-v", "error", "-select_streams", "v:0", "-show_entries",
                          "format=duration:stream=color_transfer", "-of", "json", str(film)],
                         capture_output=True, text=True)
    if res.returncode != 0:
        sys.exit(f"błąd: ffprobe nie odczytał {film}\n{res.stderr.strip()[-400:]}")
    dane = json.loads(res.stdout)
    strumienie = dane.get("streams") or [{}]
    return float(dane["format"]["duration"]), strumienie[0].get("color_transfer", "")


def podpis(tekst: str) -> str:
    """Podpis kolumny, jeśli jest czcionka; bez niej (goły worker) kolejność kolumn podaje wydruk."""
    if not FONT.is_file():
        return ""
    return f",drawtext=fontfile={FONT}:text={tekst}:x=16:y=16:fontsize=28:fontcolor=white:box=1:boxcolor=black@0.6:boxborderw=8"


def podglad(wejscie: Path, warianty: dict[str, Path], dlugosc: float, cel: Path, mem: str) -> None:
    """Rząd na moment filmu, kolumna na wariant; pierwsza kolumna to zawsze oryginał."""
    kolumny = len(warianty) + 1
    szerokosc = SZEROKOSC_PODGLADU if kolumny > 2 else 960
    skala = f"scale={szerokosc}:-2"
    wejscia, galezie = [], []
    for rzad, ulamek in enumerate(MOMENTY):
        wejscia += ["-ss", f"{dlugosc * ulamek:.3f}", "-i", str(wejscie)]
        wyjscia = "".join(f"[r{rzad}k{k}]" for k in range(kolumny))
        galezie.append(f"[{rzad}:v]split={kolumny}{wyjscia}")
        galezie.append(f"[r{rzad}k0]{skala}{podpis('przed')}[o{rzad}k0]")
        for k, (nazwa, lut) in enumerate(warianty.items(), 1):
            galezie.append(f"[r{rzad}k{k}]{filtr_lut(lut)},{skala}{podpis(nazwa)}[o{rzad}k{k}]")
        komorki = "".join(f"[o{rzad}k{k}]" for k in range(kolumny))
        galezie.append(f"{komorki}hstack=inputs={kolumny}[w{rzad}]")
    rzedy = "".join(f"[w{r}]" for r in range(len(MOMENTY)))
    galezie.append(f"{rzedy}vstack=inputs={len(MOMENTY)}[wynik]")
    proc.run(["ffmpeg", "-nostdin", "-hide_banner", "-loglevel", "error", "-y", *wejscia,
              "-filter_complex", ";".join(galezie), "-map", "[wynik]", "-frames:v", "1", "-q:v", "3", str(cel)],
             mem_max=mem, opis="podgląd przed/po")


def main() -> None:
    ap = argparse.ArgumentParser(description="C6 — korekcja barwna przez LUT")
    ap.add_argument("--work", required=True, type=Path, help="katalog roboczy")
    ap.add_argument("--in", dest="src", default="master.mp4", help="film wejściowy w katalogu roboczym")
    ap.add_argument("--out", default="kolor.mp4", help="nazwa wyniku")
    ap.add_argument("--styl", choices=sorted(STYLE), help="wbudowany styl")
    ap.add_argument("--lut", type=Path, help="własny plik .cube zamiast stylu")
    ap.add_argument("--podglad", action="store_true",
                    help="tylko klatki przed/po: wskazany wariant albo wszystkie style, bez renderu")
    ap.add_argument("--mem-max", default=proc.DOMYSLNY_LIMIT, help="limit pamięci (0 = bez limitu)")
    a = ap.parse_args()

    if a.styl and a.lut:
        sys.exit("błąd: podaj --styl albo --lut, nie oba")
    if not a.podglad and not (a.styl or a.lut):
        sys.exit("błąd: render wymaga --styl albo --lut; najpierw obejrzyj warianty przez --podglad")
    wejscie = a.work / a.src
    if not wejscie.is_file():
        sys.exit(f"błąd: nie ma pliku {wejscie}")
    if a.lut and not a.lut.is_file():
        sys.exit(f"błąd: nie ma pliku {a.lut}")

    dlugosc, transfer = zbadaj(wejscie)
    uwagi = []
    if transfer in TRANSFERY_HDR:
        uwagi.append(f"nagranie w HDR ({transfer}) — LUT-y są dla bt709, wyłącz HDR w aparacie")
        print(f"     UWAGA: {uwagi[-1]}")

    if a.lut:
        warianty = {a.lut.stem: a.lut}
    else:
        warianty = {}
        for nazwa in ([a.styl] if a.styl else sorted(STYLE)):
            warianty[nazwa] = a.work / f"kolor-{nazwa}.cube"
            zapisz_cube(STYLE[nazwa], warianty[nazwa])

    if a.podglad:
        cel = a.work / "kolor-podglad.jpg"
        podglad(wejscie, warianty, dlugosc, cel, a.mem_max)
        print(f"C6 podgląd: {cel}\n     kolumny: przed, {', '.join(warianty)}")
        return

    nazwa, lut = next(iter(warianty.items()))
    wyjscie = a.work / a.out
    print(f"C6 kolor: {nazwa} → {wyjscie}")
    proc.run(["ffmpeg", "-nostdin", "-hide_banner", "-loglevel", "error", "-y", "-i", str(wejscie),
              "-vf", filtr_lut(lut), "-c:v", "libx264", "-preset", "medium", "-crf", "18", "-pix_fmt", "yuv420p",
              "-colorspace", "bt709", "-color_primaries", "bt709", "-color_trc", "bt709", "-color_range", "tv",
              "-c:a", "copy", "-movflags", "+faststart", str(wyjscie)], mem_max=a.mem_max, opis="render korekcji")
    raport = {"wejscie": str(wejscie), "wyjscie": str(wyjscie), "wariant": nazwa, "lut": str(lut),
              "parametry": STYLE.get(a.styl) if a.styl else None, "uwagi": uwagi}
    (a.work / "kolor-raport.json").write_text(json.dumps(raport, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"     {wyjscie} + {a.work / 'kolor-raport.json'}")


if __name__ == "__main__":
    main()
