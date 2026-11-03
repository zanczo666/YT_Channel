#!/usr/bin/env python3
"""C10 + C11 — plansza końcowa i plik gotowy do wgrania.

Bierze najdalszy etap montażu (`z-grafikami.mp4`, potem `kolor.mp4`, potem `master.mp4`) i dokleja tło pod
planszę końcową. Elementy planszy (subskrypcja, następny film) ustawia się w YouTube Studio, bo API ich nie
obsługuje, więc tło zostawia dla nich wolne miejsce. Sklejamy bez ponownego kodowania filmu: to już czwarta
generacja, a ta sama jakość wymaga tu tylko zakodowania samej planszy z parametrami filmu.

    python3 scripts/finish.py --work /tmp/film-01
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path

from PIL import Image, ImageDraw

sys.path.insert(0, str(Path(__file__).resolve().parent))
import graphics  # noqa: E402 — ta sama paleta, fonty i nazwa kanału
import proc  # noqa: E402

ETAPY = ("z-grafikami.mp4", "kolor.mp4", "master.mp4")
PLANSZA_S = 10.0       # standard YouTube'a to 5–20 s; widz ma zdążyć kliknąć, a cisza nie może się dłużyć


def zbadaj(film: Path) -> dict:
    res = subprocess.run(["ffprobe", "-v", "error", "-show_entries",
                          "stream=codec_type,width,height,r_frame_rate,time_base,sample_rate,channels",
                          "-of", "json", str(film)], capture_output=True, text=True)
    if res.returncode != 0:
        sys.exit(f"błąd: ffprobe nie odczytał {film}\n{res.stderr.strip()[-400:]}")
    strumienie = {s["codec_type"]: s for s in json.loads(res.stdout)["streams"]}
    if not {"video", "audio"} <= set(strumienie):
        sys.exit(f"błąd: {film} musi mieć obraz i dźwięk")
    return strumienie


def rysuj_plansze(cel: Path, szerokosc: int, wysokosc: int) -> None:
    graphics.ustaw_rozmiar(szerokosc, wysokosc)
    obraz = Image.new("RGB", (szerokosc, wysokosc), graphics.BG)
    rysuj = ImageDraw.Draw(obraz)
    for x in range(0, szerokosc, graphics.sk(80)):
        rysuj.line([(x, 0), (x, wysokosc)], fill=graphics.GRID, width=1)
    for y in range(0, wysokosc, graphics.sk(80)):
        rysuj.line([(0, y), (szerokosc, y)], fill=graphics.GRID, width=1)
    # nazwa u góry: środek i dół kadru należą do elementów planszy końcowej
    rysuj.text((szerokosc / 2, graphics.sk(120)), graphics.NAZWA_KANALU.upper(),
               font=graphics.font(graphics.FONT_BOLD, graphics.sk(64)), fill=graphics.TEXT, anchor="mm")
    obraz.save(cel)


def main() -> None:
    ap = argparse.ArgumentParser(description="C10 + C11 — plansza końcowa i plik do wgrania")
    ap.add_argument("--work", required=True, type=Path, help="katalog roboczy")
    ap.add_argument("--in", dest="src", help="film wejściowy (domyślnie najdalszy etap montażu)")
    ap.add_argument("--out", default="final.mp4", help="nazwa wyniku")
    ap.add_argument("--plansza", type=float, default=PLANSZA_S, help="długość planszy końcowej (s)")
    ap.add_argument("--mem-max", default=proc.DOMYSLNY_LIMIT, help="limit pamięci (0 = bez limitu)")
    a = ap.parse_args()

    if not 5 <= a.plansza <= 20:
        sys.exit("błąd: plansza końcowa YouTube'a trwa od 5 do 20 s")
    nazwa = a.src or next((e for e in ETAPY if (a.work / e).is_file()), None)
    if not nazwa or not (a.work / nazwa).is_file():
        sys.exit(f"błąd: w {a.work} nie ma filmu do zakończenia; szukam: {', '.join(ETAPY)}")
    film = a.work / nazwa
    s = zbadaj(film)
    v, d = s["video"], s["audio"]

    png, klip, lista = a.work / "plansza.png", a.work / "plansza.mp4", a.work / "final-lista.txt"
    rysuj_plansze(png, v["width"], v["height"])
    uklad = "mono" if d["channels"] == 1 else "stereo"
    # parametry jak w montażu: demukser `concat` wymaga zgodnych strumieni, inaczej odtwarzacze gubią styk
    proc.run(["ffmpeg", "-nostdin", "-hide_banner", "-loglevel", "error", "-y",
              "-loop", "1", "-framerate", v["r_frame_rate"], "-t", f"{a.plansza}", "-i", str(png),
              "-f", "lavfi", "-t", f"{a.plansza}", "-i", f"anullsrc=r={d['sample_rate']}:cl={uklad}",
              "-vf", "scale=in_color_matrix=bt709:out_color_matrix=bt709,format=yuv420p",
              "-c:v", "libx264", "-preset", "medium", "-crf", "18",
              "-video_track_timescale", v["time_base"].split("/")[1],
              "-c:a", "aac", "-b:a", "192k", "-shortest", str(klip)], mem_max=a.mem_max, opis="render planszy")
    lista.write_text(f"file '{film.resolve()}'\nfile '{klip.resolve()}'\n", encoding="utf-8")
    wyjscie = a.work / a.out
    proc.run(["ffmpeg", "-nostdin", "-hide_banner", "-loglevel", "error", "-y", "-f", "concat", "-safe", "0",
              "-i", str(lista), "-c", "copy", "-movflags", "+faststart", str(wyjscie)],
             mem_max=a.mem_max, opis="doklejanie planszy")
    lista.unlink()
    (a.work / "final.json").write_text(json.dumps({"wejscie": nazwa, "plansza_s": a.plansza},
                                                  ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"OK: {nazwa} + plansza {a.plansza:.0f} s → {wyjscie}")


if __name__ == "__main__":
    main()
