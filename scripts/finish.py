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
import re
import subprocess
import sys
from pathlib import Path

from PIL import Image, ImageDraw

sys.path.insert(0, str(Path(__file__).resolve().parent))
import graphics  # noqa: E402 — ta sama paleta, fonty i nazwa kanału
import proc  # noqa: E402

ETAPY = ("z-grafikami.mp4", "kolor.mp4", "master.mp4")
PLANSZA_S = 10.0       # standard YouTube'a to 5–20 s; widz ma zdążyć kliknąć, a cisza nie może się dłużyć
INTRO_S = 3.0          # identyfikacja marki (C10, opcja --intro); dłużej zjada pierwsze sekundy, które decydują
IDENT = Path(__file__).resolve().parent.parent / "assets" / "brand" / "ident.wav"


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


def rysuj_intro(cel: Path, szerokosc: int, wysokosc: int) -> None:
    graphics.ustaw_rozmiar(szerokosc, wysokosc)
    obraz = Image.new("RGBA", (szerokosc, wysokosc), (*graphics.BG, 255))
    logo = graphics.sk(360)
    graphics.wklej_logo(obraz, (szerokosc - logo) / 2, wysokosc / 2 - logo + graphics.sk(40), logo)
    rysuj = ImageDraw.Draw(obraz)
    rysuj.text((szerokosc / 2, wysokosc / 2 + graphics.sk(120)), graphics.NAZWA_NA_BELCE.upper(),
               font=graphics.font(graphics.FONT_BOLD, graphics.sk(72)), fill=graphics.TEXT, anchor="mm")
    rysuj.text((szerokosc / 2, graphics.sk(195) + wysokosc / 2), "SYSTEMATIC TRADING LAB",
               font=graphics.font(graphics.FONT_ZWYKLY, graphics.sk(40)), fill=graphics.AKCENTY["pass"], anchor="mm")
    obraz.convert("RGB").save(cel)


def klip_z_obrazu(png: Path, cel: Path, dlugosc: float, v: dict, d: dict, mem: str,
                  dzwiek: Path | None = None, przejscie: float = 0.0) -> None:
    """Obraz + dźwięk (albo cisza) zakodowane jak film: demukser `concat` wymaga zgodnych strumieni."""
    uklad = "mono" if d["channels"] == 1 else "stereo"
    audio = (["-i", str(dzwiek)] if dzwiek and dzwiek.is_file()
             else ["-f", "lavfi", "-t", f"{dlugosc}", "-i", f"anullsrc=r={d['sample_rate']}:cl={uklad}"])
    obraz = "scale=in_color_matrix=bt709:out_color_matrix=bt709,format=yuv420p"
    if przejscie:
        obraz += f",fade=t=in:st=0:d={przejscie},fade=t=out:st={dlugosc - przejscie / 2:.3f}:d={przejscie / 2}"
    proc.run(["ffmpeg", "-nostdin", "-hide_banner", "-loglevel", "error", "-y",
              "-loop", "1", "-framerate", v["r_frame_rate"], "-t", f"{dlugosc}", "-i", str(png), *audio,
              "-vf", obraz, "-af", f"aresample={d['sample_rate']},aformat=channel_layouts={uklad},apad",
              "-t", f"{dlugosc}", "-c:v", "libx264", "-preset", "medium", "-crf", "18",
              "-video_track_timescale", v["time_base"].split("/")[1],
              "-c:a", "aac", "-b:a", "192k", str(cel)], mem_max=mem, opis=f"render {png.stem}")


def przesun_czasy(work: Path, dt: float) -> None:
    """Intro przesuwa całą treść: napisy i rozdziały liczymy od kopii sprzed przesunięcia (powtórka jest bezpieczna)."""
    for srt in work.glob("napisy-*.srt"):
        if srt.name.endswith(".bez-intro.srt"):
            continue
        kopia = srt.with_name(srt.stem + ".bez-intro.srt")
        if not kopia.is_file():
            kopia.write_text(srt.read_text(encoding="utf-8"), encoding="utf-8")
        def przesun(m: re.Match) -> str:
            g, mi, s, ms = map(int, m.groups())
            t = g * 3600 + mi * 60 + s + ms / 1000 + dt
            return f"{int(t // 3600):02d}:{int(t % 3600 // 60):02d}:{int(t % 60):02d},{round(t % 1 * 1000) % 1000:03d}"
        srt.write_text(re.sub(r"(\d\d):(\d\d):(\d\d),(\d\d\d)", przesun, kopia.read_text(encoding="utf-8")),
                       encoding="utf-8")
    plik = work / "rozdzialy.json"
    if plik.is_file():
        kopia = plik.with_name("rozdzialy.bez-intro.json")
        if not kopia.is_file():
            kopia.write_text(plik.read_text(encoding="utf-8"), encoding="utf-8")
        dane = json.loads(kopia.read_text(encoding="utf-8"))
        for i, r in enumerate(dane["rozdzialy"]):
            r["start"] = 0.0 if i == 0 else round(r["start"] + dt, 3)    # pierwszy rozdział musi zostać 0:00
            r["koniec"] = round(r["koniec"] + dt, 3)
        plik.write_text(json.dumps(dane, ensure_ascii=False, indent=2), encoding="utf-8")
        (work / "rozdzialy.txt").write_text("\n".join(
            f"{int(r['start'] // 60)}:{int(r['start'] % 60):02d} {r['nazwa']}" for r in dane["rozdzialy"]) + "\n",
            encoding="utf-8")


def main() -> None:
    ap = argparse.ArgumentParser(description="C10 + C11 — plansza końcowa i plik do wgrania")
    ap.add_argument("--work", required=True, type=Path, help="katalog roboczy")
    ap.add_argument("--in", dest="src", help="film wejściowy (domyślnie najdalszy etap montażu)")
    ap.add_argument("--out", default="final.mp4", help="nazwa wyniku")
    ap.add_argument("--plansza", type=float, default=PLANSZA_S, help="długość planszy końcowej (s)")
    ap.add_argument("--intro", action="store_true", help=f"{INTRO_S:.0f} s identyfikacji marki na początku")
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
    klip_z_obrazu(png, klip, a.plansza, v, d, a.mem_max)
    czesci = [film, klip]
    if a.intro:
        intro_png, intro = a.work / "intro.png", a.work / "intro.mp4"
        rysuj_intro(intro_png, v["width"], v["height"])
        klip_z_obrazu(intro_png, intro, INTRO_S, v, d, a.mem_max, IDENT, przejscie=0.6)
        czesci.insert(0, intro)
    przesun_czasy(a.work, INTRO_S if a.intro else 0.0)
    lista.write_text("".join(f"file '{c.resolve()}'\n" for c in czesci), encoding="utf-8")
    wyjscie = a.work / a.out
    proc.run(["ffmpeg", "-nostdin", "-hide_banner", "-loglevel", "error", "-y", "-f", "concat", "-safe", "0",
              "-i", str(lista), "-c", "copy", "-movflags", "+faststart", str(wyjscie)],
             mem_max=a.mem_max, opis="sklejanie z planszą")
    lista.unlink()
    (a.work / "final.json").write_text(json.dumps({"wejscie": nazwa, "plansza_s": a.plansza,
                                                   "intro_s": INTRO_S if a.intro else 0.0},
                                                  ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"OK: {nazwa} + plansza {a.plansza:.0f} s → {wyjscie}")


if __name__ == "__main__":
    main()
