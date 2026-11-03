#!/usr/bin/env python3
"""C12 — kontrola jakości gotowego pliku przed wgraniem.

Sprawdza to, co da się zmierzyć: format, zgodność obrazu z dźwiękiem, błędy dekodowania, czarne klatki,
długą ciszę, głośność, napisy i rozdziały. Zapisuje `qc.json` oraz `qc-klatki.jpg`, czyli siatkę klatek do
obejrzenia (grafika na twarzy, mignięcia), bo tego pomiary nie wyłapią.

Domyślnie kończy się kodem 0 także przy błędach: worker musi zdążyć zabrać wyniki przed skasowaniem maszyny.
`--strict` daje kod 1 przy werdykcie FAIL.

    python3 scripts/qc.py --work /tmp/film-01
"""

from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import proc  # noqa: E402

CEL_LUFS, CEL_TP = -14.0, -1.5
TOL_LUFS_OK, TOL_LUFS_MAX = 1.0, 2.0
TP_MAX = -1.0
ROZJAZD_AV = 0.1          # sekundy między końcem obrazu i dźwięku
ROZJAZD_OSI = 0.5         # sekundy między planem z cut.json a plikiem
CISZA_MAX_S = 2.0
KLATEK_NA_SIATCE = 24
DLUGOSC_MIN_S, DLUGOSC_MAX_S = 360, 600   # pierwsze filmy: 6–10 min, sama uwaga
BLAD_DEKODOWANIA = re.compile(r"corrupt|invalid|error while decoding|non-existing|missing picture", re.I)


def sekundy_srt(t: str) -> float:
    g, m, s = t.replace(",", ".").split(":")
    return int(g) * 3600 + int(m) * 60 + float(s)


def wpisy_srt(sciezka: Path) -> list[tuple[float, float]]:
    bloki = sciezka.read_text(encoding="utf-8").strip().split("\n\n")
    wynik = []
    for b in bloki:
        linie = b.splitlines()
        if len(linie) >= 2 and " --> " in linie[1]:
            od, do = linie[1].split(" --> ")
            wynik.append((sekundy_srt(od), sekundy_srt(do)))
    return wynik


def main() -> None:
    ap = argparse.ArgumentParser(description="C12 — kontrola jakości gotowego pliku")
    ap.add_argument("--work", required=True, type=Path, help="katalog roboczy")
    ap.add_argument("--in", dest="src", default="final.mp4", help="film do sprawdzenia")
    ap.add_argument("--strict", action="store_true", help="kod wyjścia 1 przy werdykcie FAIL")
    ap.add_argument("--mem-max", default=proc.DOMYSLNY_LIMIT, help="limit pamięci (0 = bez limitu)")
    a = ap.parse_args()

    film = a.work / a.src
    if not film.is_file():
        sys.exit(f"błąd: nie ma pliku {film} — najpierw uruchom finish.py")
    bledy: list[str] = []
    uwagi: list[str] = []

    res = subprocess.run(["ffprobe", "-v", "error", "-show_entries",
                          "format=duration:stream=codec_type,codec_name,width,height,pix_fmt,avg_frame_rate,"
                          "sample_rate,duration", "-of", "json", str(film)], capture_output=True, text=True)
    if res.returncode != 0:
        sys.exit(f"błąd: ffprobe nie odczytał {film}\n{res.stderr.strip()[-400:]}")
    dane = json.loads(res.stdout)
    strumienie = {s["codec_type"]: s for s in dane["streams"]}
    if not {"video", "audio"} <= set(strumienie):
        sys.exit(f"błąd: {film} musi mieć obraz i dźwięk")
    v, d = strumienie["video"], strumienie["audio"]
    dlugosc = float(dane["format"]["duration"])

    if (v["codec_name"], v["pix_fmt"]) != ("h264", "yuv420p"):
        bledy.append(f"obraz {v['codec_name']}/{v['pix_fmt']}, oczekiwane h264/yuv420p")
    if (v["width"], v["height"]) != (1920, 1080):
        bledy.append(f"rozdzielczość {v['width']}×{v['height']}, oczekiwane 1920×1080")
    licznik, mianownik = v["avg_frame_rate"].split("/")
    fps = int(licznik) / int(mianownik)
    if abs(fps - 30) > 0.1:
        uwagi.append(f"{fps:.2f} kl./s, standard to 30")
    if (d["codec_name"], d["sample_rate"]) != ("aac", "48000"):
        bledy.append(f"dźwięk {d['codec_name']}/{d['sample_rate']} Hz, oczekiwane aac/48000")
    rozjazd = abs(float(v.get("duration", dlugosc)) - float(d.get("duration", dlugosc)))
    if rozjazd > ROZJAZD_AV:
        bledy.append(f"obraz i dźwięk kończą się w odstępie {rozjazd:.2f} s")
    if not DLUGOSC_MIN_S <= dlugosc <= DLUGOSC_MAX_S:
        uwagi.append(f"długość {dlugosc / 60:.1f} min, plan na pierwsze filmy to 6–10 min")

    final = a.work / "final.json"
    plansza = json.loads(final.read_text(encoding="utf-8"))["plansza_s"] if final.is_file() else 0.0
    koniec_tresci = dlugosc - plansza
    cut_path = a.work / "cut.json"
    if cut_path.is_file():
        plan = json.loads(cut_path.read_text(encoding="utf-8"))["dlugosc_s"]
        if abs(plan - koniec_tresci) > ROZJAZD_OSI:
            bledy.append(f"oś czasu {plan:.2f} s, a treść w pliku {koniec_tresci:.2f} s: napisy się rozjadą")
    else:
        uwagi.append("brak cut.json, nie sprawdzam osi czasu")

    # jedno przejście przez cały plik; pełny log, bo liczą się w nim pomiary filtrów i błędy dekodera
    przebieg = proc.run(["ffmpeg", "-nostdin", "-hide_banner", "-nostats", "-i", str(film),
                         "-vf", "blackdetect=d=0.5:pix_th=0.10", "-af",
                         f"silencedetect=noise=-50dB:d={CISZA_MAX_S},ebur128=peak=true",
                         "-f", "null", "-"], mem_max=a.mem_max, opis="pomiar pliku").stderr
    bledne = [l for l in przebieg.splitlines() if BLAD_DEKODOWANIA.search(l) and "Parsed_" not in l]
    if bledne:
        bledy.append(f"błędy dekodowania: {len(bledne)}, np. {bledne[0].strip()[:120]}")
    czarne = re.findall(r"black_start:([\d.]+) black_end:([\d.]+)", przebieg)
    if czarne:
        bledy.append("czarne klatki: " + ", ".join(f"{float(o):.1f}–{float(k):.1f} s" for o, k in czarne[:5]))
    cisze = [float(x) for x in re.findall(r"silence_start: ([\d.]+)", przebieg)]
    w_tresci = [c for c in cisze if c < koniec_tresci - 0.5]
    if w_tresci:
        uwagi.append("cisza ponad " + f"{CISZA_MAX_S:.0f} s od: " + ", ".join(f"{c:.1f} s" for c in w_tresci[:5]))
    podsumowanie = przebieg[przebieg.rfind("Summary:"):]
    lufs = re.search(r"I:\s+(-?[\d.]+) LUFS", podsumowanie)
    tp = re.search(r"Peak:\s+(-?[\d.]+) dBFS", podsumowanie)
    if not lufs or not tp:
        bledy.append("nie udało się zmierzyć głośności")
    else:
        odchylka = abs(float(lufs[1]) - CEL_LUFS)
        if odchylka > TOL_LUFS_MAX:
            bledy.append(f"głośność {lufs[1]} LUFS, cel {CEL_LUFS}")
        elif odchylka > TOL_LUFS_OK:
            uwagi.append(f"głośność {lufs[1]} LUFS, cel {CEL_LUFS}")
        if float(tp[1]) > TP_MAX:
            bledy.append(f"szczyt {tp[1]} dBTP ponad limitem {TP_MAX}")

    for jezyk in ("en", "pl"):
        srt = a.work / f"napisy-{jezyk}.srt"
        if not srt.is_file():
            bledy.append(f"brak napisów {jezyk.upper()}")
            continue
        wpisy = wpisy_srt(srt)
        if not wpisy:
            bledy.append(f"puste napisy {jezyk.upper()}")
            continue
        if any(wpisy[i][1] > wpisy[i + 1][0] for i in range(len(wpisy) - 1)):
            bledy.append(f"napisy {jezyk.upper()} nachodzą na siebie")
        if wpisy[-1][1] > dlugosc:
            bledy.append(f"napisy {jezyk.upper()} kończą się po końcu filmu")

    rozdzialy_path = a.work / "rozdzialy.json"
    if not rozdzialy_path.is_file():
        bledy.append("brak rozdziałów")
    else:
        rozdzialy = json.loads(rozdzialy_path.read_text(encoding="utf-8"))["rozdzialy"]
        if len(rozdzialy) < 3 or rozdzialy[0]["start"] != 0:
            bledy.append("rozdziały: YouTube wymaga startu od 0:00 i co najmniej trzech")
        krotkie = [r["nazwa"] for r in rozdzialy if r["koniec"] - r["start"] < 10]
        if krotkie:
            bledy.append("rozdziały krótsze niż 10 s: " + ", ".join(krotkie))

    siatka = a.work / "qc-klatki.jpg"
    krok = max(dlugosc / KLATEK_NA_SIATCE, 0.1)
    proc.run(["ffmpeg", "-nostdin", "-hide_banner", "-loglevel", "error", "-y", "-i", str(film),
              "-vf", f"fps=1/{krok:.3f},scale=480:-2,tile=6x4", "-frames:v", "1", "-q:v", "4", str(siatka)],
             mem_max=a.mem_max, opis="siatka klatek")

    werdykt = "FAIL" if bledy else ("UWAGI" if uwagi else "OK")
    raport = {"film": a.src, "werdykt": werdykt, "dlugosc_s": round(dlugosc, 2), "plansza_s": plansza,
              "lufs": float(lufs[1]) if lufs else None, "szczyt_dbtp": float(tp[1]) if tp else None,
              "bledy": bledy, "uwagi": uwagi}
    (a.work / "qc.json").write_text(json.dumps(raport, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"C12 {werdykt}: {a.src}, {dlugosc:.1f} s, {raport['lufs']} LUFS, {raport['szczyt_dbtp']} dBTP")
    for b in bledy:
        print(f"     BŁĄD: {b}")
    for u in uwagi:
        print(f"     uwaga: {u}")
    print(f"     {a.work / 'qc.json'} + {siatka}")
    if a.strict and bledy:
        sys.exit(1)


if __name__ == "__main__":
    main()
