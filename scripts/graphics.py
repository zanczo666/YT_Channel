#!/usr/bin/env python3
"""C7 — ekrany i grafiki: plan z kolumny „Na ekranie”, szablony z danych, nałożenie na montaż.

Trzy kroki w jednym przebiegu:

1. **Plan.** Kolumna „Na ekranie” w scenariuszu mówi, co widać przy którym zdaniu (`GRAFIKA: equity`,
   `EKRAN: kod`, `TWARZ`, `—`). Sąsiednie zdania z tym samym poleceniem to jeden plan zdjęciowy;
   czasy bierzemy z `cut.json`, czyli z rzeczywistego montażu.
2. **Szablony.** Grafikę rysuje Pillow z **danych podanych w pliku** (`--dane`), nigdy z niczego:
   liczby w materiale publicznym wolno brać wyłącznie z Ledgera i kart fabryki. Brak danych dla planu
   to błąd, a nie zachęta do wymyślenia wykresu. Szablon jest wielokrotnego użytku — nie generujemy
   grafiki od zera pod każdy film (koszt tokenów, brak spójności wizualnej).
3. **Nałożenie.** Jedno przejście FFmpeg: grafiki wchodzą i schodzą przenikaniem, zasłaniając twarz
   dokładnie tam, gdzie wypada sklejka — to jest właściwe rozwiązanie „sztywnego montażu”,
   a nie naprzemienne przybliżenie z C4 (`content/notes/_test-nagranie-cut1.md`).

    python3 scripts/graphics.py --work /tmp/film-01 --script content/scripts/<slug>.md --dane dane.json

Format `--dane`: słownik `ID zdania` (albo nazwa motywu) → opis grafiki. Każdy wpis ma `typ`
(`equity`, `lejek`, `metryki`, `cytat`), `tytul`, `zrodlo` (skąd liczby) i pola właściwe dla typu.
`zrodlo: "test"` wypala na grafice znak wodny DANE TESTOWE — żeby taki materiał nie trafił na kanał.

`BELKA: subscribe` w kolumnie „Na ekranie” to mała belka nad twarzą, bez danych z `--dane`. Stawiamy ją raz
na film, przy zdaniu z CTA (`docs/YT_PUBLISHING_STANDARD.md` §9).
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

sys.path.insert(0, str(Path(__file__).resolve().parent))
import proc  # noqa: E402

# ta sama paleta i te same fonty co miniatury — kanał ma wyglądać na jeden kanał
BG = (13, 19, 30)
GRID = (30, 40, 56)
TEXT = (245, 247, 250)
PRZYGASZONY = (150, 163, 182)
AKCENTY = {"pass": (110, 231, 140), "fail": (255, 92, 92), "neutral": (255, 196, 61)}
FONT_BOLD = "/usr/share/fonts/opentype/urw-base35/NimbusSansNarrow-Bold.otf"
FONT_ZWYKLY = "/usr/share/fonts/opentype/urw-base35/NimbusSans-Regular.otf"

# Rozmiar grafiki bierzemy z samego filmu, a nie na sztywno: nagranie telefonem bywa pionowe,
# a grafika 1920×1080 nałożona na kadr 608×1080 jest po prostu obcięta (tak wyszło przy pierwszym teście).
SZEROKOSC, WYSOKOSC = 1920, 1080
SKALA = 1.0
MARGINES = 110


def ustaw_rozmiar(szerokosc: int, wysokosc: int) -> None:
    """Wszystkie wymiary w szablonach są liczone dla kadru 1920×1080 i skalowane do rzeczywistego."""
    global SZEROKOSC, WYSOKOSC, SKALA, MARGINES
    SZEROKOSC, WYSOKOSC = szerokosc, wysokosc
    SKALA = min(szerokosc / 1920, wysokosc / 1080)
    MARGINES = round(110 * SKALA)


def sk(wartosc: float) -> int:
    """Rozmiar (czcionki, odstępu) przeskalowany do kadru."""
    return max(1, round(wartosc * SKALA))
PRZENIKANIE = 0.35          # sekundy wejścia i zejścia grafiki
MIN_PLAN_S = 1.2            # krótszy błysk grafiki męczy, zamiast pomagać
DLUGOSC_BELKI = 4.0         # tyle zajmuje przeczytanie; dłużej zaczyna przeszkadzać
NAZWA_KANALU = "Systematic Trading Research"
CZERWIEN_SUBSKRYPCJI = (204, 0, 0)

WIERSZ_EKRAN = re.compile(r"^\|\s*(L\d{3,})\s*\|[^|]*\|[^|]*\|([^|]*)\|", re.MULTILINE)


def rozmiar_kadru(film: Path) -> tuple[int, int]:
    res = proc.run(["ffprobe", "-v", "error", "-select_streams", "v", "-show_entries",
                    "stream=width,height", "-of", "csv=p=0:s=x", str(film)], mem_max=None, opis="rozmiar kadru")
    szer, wys = res.stdout.strip().splitlines()[0].split("x")
    return int(szer), int(wys)


def font(sciezka: str, rozmiar: int) -> ImageFont.FreeTypeFont:
    try:
        return ImageFont.truetype(sciezka, rozmiar)
    except OSError:
        return ImageFont.load_default()


def plan_z_scenariusza(script: Path, cut: dict) -> list[dict]:
    """Sąsiednie zdania z tym samym poleceniem „Na ekranie” → jeden plan, z czasami z montażu."""
    polecenia = {m.group(1): m.group(2).strip() for m in WIERSZ_EKRAN.finditer(script.read_text(encoding="utf-8"))}
    plany: list[dict] = []
    for odcinek in cut["os_czasu"]:
        polecenie = polecenia.get(odcinek["id"], "")
        if polecenie in ("", "—", "-", "TWARZ"):
            continue
        rodzaj, _, co = polecenie.partition(":")
        wpis = {"rodzaj": rodzaj.strip().upper(), "co": co.strip() or rodzaj.strip(),
                "od": odcinek["montaz_start"], "do": odcinek["montaz_koniec"], "zdania": [odcinek["id"]]}
        if plany and plany[-1]["rodzaj"] == wpis["rodzaj"] and plany[-1]["co"] == wpis["co"] \
                and abs(plany[-1]["do"] - wpis["od"]) < 0.05:
            plany[-1]["do"] = wpis["do"]
            plany[-1]["zdania"].append(odcinek["id"])
        else:
            plany.append(wpis)
    for p in plany:
        if p["rodzaj"] == "BELKA":               # czas belki nie zależy od długości zdania
            p["do"] = min(p["od"] + DLUGOSC_BELKI, cut["dlugosc_s"])
    return [p for p in plany if p["do"] - p["od"] >= MIN_PLAN_S]


def tytul(rysuj: ImageDraw.ImageDraw, tekst: str) -> None:
    """Tytuł u góry, łamany do szerokości kadru — w pionowym kadrze jedna linia się nie mieści."""
    if not tekst:
        return
    f = font(FONT_BOLD, sk(64))
    linie, biezaca = [], ""
    for slowo in tekst.upper().split():
        kandydat = f"{biezaca} {slowo}".strip()
        if rysuj.textlength(kandydat, font=f) > SZEROKOSC - 2 * MARGINES and biezaca:
            linie.append(biezaca); biezaca = slowo
        else:
            biezaca = kandydat
    linie.append(biezaca)
    y = sk(70)
    for linia in linie:
        rysuj.text((MARGINES, y), linia, font=f, fill=TEXT)
        y += sk(72)


def ramka(rysuj: ImageDraw.ImageDraw, dane: dict) -> None:
    """Wspólne dla wszystkich szablonów: siatka, tytuł, podpis ze źródłem liczb."""
    for x in range(0, SZEROKOSC, sk(80)):
        rysuj.line([(x, 0), (x, WYSOKOSC)], fill=GRID, width=1)
    for y in range(0, WYSOKOSC, sk(80)):
        rysuj.line([(0, y), (SZEROKOSC, y)], fill=GRID, width=1)
    tytul(rysuj, dane.get("tytul", ""))
    zrodlo = dane.get("zrodlo", "")
    if zrodlo:
        podpis = "DANE TESTOWE — NIE DO PUBLIKACJI" if zrodlo == "test" else f"źródło: {zrodlo}"
        rysuj.text((MARGINES, WYSOKOSC - sk(70)), podpis, font=font(FONT_ZWYKLY, sk(28)),
                   fill=AKCENTY["fail"] if zrodlo == "test" else PRZYGASZONY)


def rysuj_equity(rysuj: ImageDraw.ImageDraw, dane: dict, akcent: tuple[int, int, int]) -> None:
    """Krzywa kapitału z pionową linią podziału: co model widział, a czego nie."""
    seria_is = [float(v) for v in dane.get("is", [])]
    seria_oos = [float(v) for v in dane.get("oos", [])]
    if len(seria_is) < 2 or len(seria_oos) < 2:
        sys.exit("błąd: equity wymaga co najmniej dwóch punktów w `is` i w `oos`")
    wszystkie = seria_is + seria_oos
    lo, hi = min(wszystkie), max(wszystkie)
    rozpietosc = (hi - lo) or 1.0
    x0, x1 = MARGINES, SZEROKOSC - MARGINES
    y0, y1 = sk(230), WYSOKOSC - sk(180)
    # w wąskim kadrze pole wykresu samo z siebie byłoby pionowym paskiem, a na nim każdy ruch
    # equity wygląda dramatycznie — trzymamy proporcję nie wyższą niż 2:3 i centrujemy
    if (y1 - y0) > (x1 - x0) * 1.5:
        wysokosc_pola = (x1 - x0) * 1.5
        srodek = (y0 + y1) / 2
        y0, y1 = srodek - wysokosc_pola / 2, srodek + wysokosc_pola / 2

    def punkt(i: int, v: float) -> tuple[float, float]:
        x = x0 + (x1 - x0) * i / (len(wszystkie) - 1)
        return x, y1 - (y1 - y0) * (v - lo) / rozpietosc

    punkty = [punkt(i, v) for i, v in enumerate(wszystkie)]
    granica = punkty[len(seria_is) - 1][0]
    rysuj.line([(granica, y0 - sk(30)), (granica, y1)], fill=PRZYGASZONY, width=2)
    rysuj.line(punkty[:len(seria_is)], fill=TEXT, width=sk(6), joint="curve")
    rysuj.line(punkty[len(seria_is) - 1:], fill=akcent, width=sk(6), joint="curve")
    rysuj.text((x0 + sk(16), y0 - sk(46)), "IN SAMPLE", font=font(FONT_BOLD, sk(30)), fill=PRZYGASZONY)
    rysuj.text((granica + sk(16), y0 - sk(46)), "OUT OF SAMPLE", font=font(FONT_BOLD, sk(30)), fill=akcent)


def rysuj_lejek(rysuj: ImageDraw.ImageDraw, dane: dict, akcent: tuple[int, int, int]) -> None:
    """Etapy lejka jako malejące słupki — ile weszło, ile przeżyło każdy etap."""
    etapy = dane.get("etapy", [])
    if not etapy:
        sys.exit("błąd: lejek wymaga listy `etapy` [{nazwa, ile}]")
    najwieksza = max(float(e["ile"]) for e in etapy) or 1.0
    y = sk(250)
    wysokosc = min(sk(96), (WYSOKOSC - sk(420)) // max(1, len(etapy)))
    for i, e in enumerate(etapy):
        szer = (SZEROKOSC - 2 * MARGINES - sk(360)) * float(e["ile"]) / najwieksza
        kolor = akcent if i == len(etapy) - 1 else (58, 76, 102)
        rysuj.rectangle([MARGINES + sk(360), y, MARGINES + sk(360) + szer, y + wysokosc - sk(18)], fill=kolor)
        rysuj.text((MARGINES, y + sk(6)), str(e["nazwa"]).upper(), font=font(FONT_BOLD, sk(34)), fill=TEXT)
        rysuj.text((MARGINES + sk(372) + szer, y + sk(6)), str(e["ile"]), font=font(FONT_BOLD, sk(34)), fill=TEXT)
        y += wysokosc


def rysuj_metryki(rysuj: ImageDraw.ImageDraw, dane: dict, akcent: tuple[int, int, int]) -> None:
    """Tabela liczb: nazwa po lewej, wartość po prawej. Najwyżej sześć wierszy — więcej nikt nie przeczyta."""
    wiersze = dane.get("wiersze", [])[:6]
    if not wiersze:
        sys.exit("błąd: metryki wymagają listy `wiersze` [{nazwa, wartosc}] albo [[nazwa, wartosc]]")
    y = sk(280)
    for w in wiersze:
        nazwa, wartosc = (w["nazwa"], w["wartosc"]) if isinstance(w, dict) else w
        rysuj.text((MARGINES, y), str(nazwa).upper(), font=font(FONT_ZWYKLY, sk(44)), fill=PRZYGASZONY)
        tekst = str(wartosc)
        szer = rysuj.textlength(tekst, font=font(FONT_BOLD, sk(56)))
        rysuj.text((SZEROKOSC - MARGINES - szer, y - sk(8)), tekst, font=font(FONT_BOLD, sk(56)), fill=akcent)
        y += sk(108)
        rysuj.line([(MARGINES, y - sk(26)), (SZEROKOSC - MARGINES, y - sk(26))], fill=GRID, width=2)


def rysuj_cytat(rysuj: ImageDraw.ImageDraw, dane: dict, akcent: tuple[int, int, int]) -> None:
    """Zdanie z publikacji albo z karty, z podaniem, czyje ono jest."""
    tresc = dane.get("tresc", "")
    if not tresc:
        sys.exit("błąd: cytat wymaga pola `tresc`")
    f = font(FONT_BOLD, sk(64))
    linie, biezaca = [], ""
    for slowo in tresc.split():
        kandydat = f"{biezaca} {slowo}".strip()
        if rysuj.textlength(kandydat, font=f) > SZEROKOSC - 2 * MARGINES and biezaca:
            linie.append(biezaca); biezaca = slowo
        else:
            biezaca = kandydat
    linie.append(biezaca)
    y = (WYSOKOSC - len(linie) * sk(86)) // 2
    for linia in linie:
        rysuj.text((MARGINES, y), linia, font=f, fill=TEXT)
        y += sk(86)
    if dane.get("autor"):
        rysuj.text((MARGINES, y + sk(24)), f"— {dane['autor']}", font=font(FONT_ZWYKLY, sk(40)), fill=akcent)


SZABLONY = {"equity": rysuj_equity, "lejek": rysuj_lejek, "metryki": rysuj_metryki, "cytat": rysuj_cytat}


def renderuj(dane: dict, cel: Path) -> None:
    typ = dane.get("typ")
    if typ not in SZABLONY:
        sys.exit(f"błąd: nieznany typ grafiki „{typ}”; mamy: {', '.join(sorted(SZABLONY))}")
    obraz = Image.new("RGB", (SZEROKOSC, WYSOKOSC), BG)
    rysuj = ImageDraw.Draw(obraz)
    ramka(rysuj, dane)
    SZABLONY[typ](rysuj, dane, AKCENTY.get(dane.get("werdykt", "neutral"), AKCENTY["neutral"]))
    obraz.save(cel)


def renderuj_belke(cel: Path) -> None:
    """Mała belka z lewej, nad strefą napisów i paska odtwarzacza. Przezroczysta — twarz zostaje widoczna."""
    obraz = Image.new("RGBA", (SZEROKOSC, WYSOKOSC), (0, 0, 0, 0))
    rysuj = ImageDraw.Draw(obraz)
    f_nazwa, f_przycisk = font(FONT_BOLD, sk(36)), font(FONT_BOLD, sk(34))
    wys, odstep = sk(76), sk(22)
    szer_nazwy = rysuj.textlength(NAZWA_KANALU, font=f_nazwa)
    szer_przycisku = rysuj.textlength("SUBSCRIBE", font=f_przycisk) + 2 * sk(26)
    x0, y0 = MARGINES, WYSOKOSC - sk(280)
    x1 = x0 + odstep + szer_nazwy + odstep + szer_przycisku + sk(10)
    rysuj.rounded_rectangle([x0, y0, x1, y0 + wys], radius=sk(14), fill=(*BG, 225))
    rysuj.text((x0 + odstep, y0 + wys / 2), NAZWA_KANALU, font=f_nazwa, fill=TEXT, anchor="lm")
    px0 = x1 - sk(10) - szer_przycisku
    rysuj.rounded_rectangle([px0, y0 + sk(10), x1 - sk(10), y0 + wys - sk(10)], radius=sk(10), fill=CZERWIEN_SUBSKRYPCJI)
    rysuj.text(((px0 + x1 - sk(10)) / 2, y0 + wys / 2), "SUBSCRIBE", font=f_przycisk, fill=TEXT, anchor="mm")
    obraz.save(cel)


def naloz(wejscie: Path, plany: list[dict], wyjscie: Path, mem: str) -> None:
    """Jedno przejście FFmpeg: każda grafika wchodzi i schodzi przenikaniem w swoim czasie."""
    wejscia: list[str] = ["-i", str(wejscie)]
    for p in plany:
        wejscia += ["-loop", "1", "-t", f"{p['do'] - p['od'] + 2 * PRZENIKANIE:.3f}", "-i", str(p["plik"])]

    kroki, biezacy = [], "[0:v]"
    for i, p in enumerate(plany, 1):
        dlugosc = p["do"] - p["od"] + 2 * PRZENIKANIE
        kroki.append(f"[{i}:v]format=rgba,"
                     f"fade=t=in:st=0:d={PRZENIKANIE}:alpha=1,"
                     f"fade=t=out:st={dlugosc - PRZENIKANIE:.3f}:d={PRZENIKANIE}:alpha=1,"
                     f"setpts=PTS-STARTPTS+{max(0.0, p['od'] - PRZENIKANIE):.3f}/TB[g{i}]")
        wynik = f"[v{i}]" if i < len(plany) else "[out]"
        kroki.append(f"{biezacy}[g{i}]overlay=0:0:eof_action=pass{wynik}")
        biezacy = wynik

    proc.run(["ffmpeg", "-nostdin", "-hide_banner", "-loglevel", "error", "-y", *wejscia,
              "-filter_complex", ";".join(kroki), "-map", "[out]", "-map", "0:a",
              "-c:v", "libx264", "-preset", "medium", "-crf", "18", "-pix_fmt", "yuv420p",
              "-c:a", "copy", str(wyjscie)], mem_max=mem, opis="nakładanie grafik")


def main() -> None:
    ap = argparse.ArgumentParser(description="C7 — ekrany i grafiki")
    ap.add_argument("--work", required=True, type=Path, help="katalog roboczy (z cut.json)")
    ap.add_argument("--script", required=True, type=Path, help="content/scripts/<slug>.md")
    ap.add_argument("--dane", type=Path, help="JSON z danymi do grafik (ID zdania lub nazwa motywu → opis)")
    ap.add_argument("--in", dest="src", default="master.mp4", help="film wejściowy w katalogu roboczym")
    ap.add_argument("--out", default="z-grafikami.mp4", help="nazwa wyniku")
    ap.add_argument("--tylko-plan", action="store_true", help="wypisz plan zdjęciowy i zakończ")
    ap.add_argument("--mem-max", default=proc.DOMYSLNY_LIMIT, help="limit pamięci (0 = bez limitu)")
    a = ap.parse_args()

    cut_path = a.work / "cut.json"
    if not cut_path.is_file():
        sys.exit(f"błąd: brak {cut_path} — najpierw uruchom cut.py")
    cut = json.loads(cut_path.read_text(encoding="utf-8"))
    plany = plan_z_scenariusza(a.script, cut)
    (a.work / "grafiki.json").write_text(json.dumps({"plany": plany}, ensure_ascii=False, indent=2),
                                         encoding="utf-8")
    if not plany:
        print("OK: scenariusz nie przewiduje grafik ani ekranów — nie ma czego nakładać")
        return

    for p in plany:
        print(f"     {p['od']:6.1f}–{p['do']:5.1f} s  {p['rodzaj']}: {p['co']}  ({', '.join(p['zdania'])})")
    if a.tylko_plan:
        return

    src = a.work / a.src
    if not src.is_file():
        sys.exit(f"błąd: nie ma pliku {src} — najpierw uruchom cut.py i audio_master.py")
    ustaw_rozmiar(*rozmiar_kadru(src))

    dane = json.loads(a.dane.read_text(encoding="utf-8")) if a.dane and a.dane.is_file() else {}
    katalog = a.work / "grafiki"
    katalog.mkdir(exist_ok=True)

    gotowe, pominiete = [], []
    for i, p in enumerate(plany):
        if p["rodzaj"] == "BELKA":
            plik = katalog / f"{i:02d}-belka.png"
            renderuj_belke(plik)
            p["plik"] = str(plik); gotowe.append(p); continue
        opis = next((dane[k] for k in (*p["zdania"], p["co"]) if k in dane), None)
        if p["rodzaj"] == "EKRAN" and isinstance(opis, str):      # gotowy zrzut albo nagranie ekranu
            p["plik"] = str(Path(opis).resolve()); gotowe.append(p); continue
        if not opis:
            pominiete.append(p); continue
        plik = katalog / f"{i:02d}-{p['zdania'][0]}.png"
        renderuj(opis, plik)
        p["plik"] = str(plik)
        gotowe.append(p)

    for p in pominiete:
        print(f"     brak danych do „{p['co']}” ({', '.join(p['zdania'])}) — plan zostaje pusty")

    if not gotowe:
        sys.exit("błąd: żaden plan nie ma danych — liczby i wykresy biorą się z Ledgera i kart, "
                 "nie z niczego; uzupełnij --dane")

    naloz(src, gotowe, a.work / a.out, a.mem_max)
    print(f"OK: {len(gotowe)} grafik nałożonych"
          + (f", {len(pominiete)} planów bez danych" if pominiete else ""))
    print(f"     {a.work / a.out} + {a.work / 'grafiki.json'}")


if __name__ == "__main__":
    main()
