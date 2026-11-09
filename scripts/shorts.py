#!/usr/bin/env python3
"""C13 — shorts 9:16 z zakresów ID zdań, z napisami wypalonymi słowo po słowie.

Zakresy wybiera agent `yt-producer` w `content/publish/<slug>/shorts.json` (`od`, `do`, `tytul`, `opis`).
Czasy bierzemy z osi montażu (`cut.json`), tekst ze scenariusza, a moment każdego słowa z transkrypcji,
tak jak w napisach C8. Obraz to wycinek 9:16 z montażu bez grafik, bo grafiki 16:9 po przycięciu są nieczytelne.

    python3 scripts/shorts.py --work ~/film/<slug> --script content/scripts/<slug>.md --pakiet content/publish/<slug>
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import proc  # noqa: E402
from align import czytaj_scenariusz, tokenizuj  # noqa: E402
from subtitles import POKRYCIE_SLOW, czasy_slow  # noqa: E402

PROJEKT = Path(__file__).resolve().parent.parent
MAX_S = 59.0
SLOW_W_GRUPIE = 3
SZER, WYS = 1080, 1920
ZIELONY_ASS = "&H008CE76E"     # #6EE78C zapisany jako BGR, jak chce ASS


def czasy_zdania(zdanie: dict, odcinek: dict, slowa: list[dict]) -> list[tuple[float, float]]:
    """Czas każdego słowa scenariusza w osi montażu (ta sama logika co w napisach C8)."""
    tekst = zdanie["en"].split()
    w_odcinku = [w for w in slowa if w["start"] >= odcinek["zrodlo_start"] - 0.01
                 and w["koniec"] <= odcinek["zrodlo_koniec"] + 0.01]
    przesuniecie = odcinek["montaz_start"] - odcinek["zrodlo_start"]
    czasy = czasy_slow(tokenizuj(zdanie["en"]), w_odcinku) if w_odcinku else []
    if len(czasy) != len(tekst) or len(w_odcinku) < POKRYCIE_SLOW * len(tekst):
        od, do = odcinek["montaz_start"] + 0.25, odcinek["montaz_koniec"] - 0.4
        krok = (do - od) / max(1, len(tekst))
        return [(od + i * krok, od + (i + 1) * krok) for i in range(len(tekst))]
    return [(a + przesuniecie, b + przesuniecie) for a, b in czasy]


def czas_ass(s: float) -> str:
    s = max(0.0, s)
    return f"{int(s // 3600)}:{int(s % 3600 // 60):02d}:{s % 60:05.2f}"


def napisy_ass(slowa_czasy: list[tuple[str, float, float]], cel: Path) -> None:
    """Grupy po trzy słowa; aktualnie wypowiadane jest zielone."""
    linie = ["[Script Info]", "ScriptType: v4.00+", f"PlayResX: {SZER}", f"PlayResY: {WYS}", "",
             "[V4+ Styles]",
             "Format: Name, Fontname, Fontsize, PrimaryColour, OutlineColour, BackColour, Bold, BorderStyle, "
             "Outline, Shadow, Alignment, MarginL, MarginR, MarginV",
             "Style: Slowa,Anton,112,&H00FAF7F5,&H001E130D,&H00000000,0,1,6,0,2,80,80,620", "",
             "[Events]", "Format: Layer, Start, End, Style, Text"]
    for i, (_, od, do) in enumerate(slowa_czasy):
        poczatek = i - i % SLOW_W_GRUPIE
        grupa = slowa_czasy[poczatek:poczatek + SLOW_W_GRUPIE]
        tekst = " ".join(("{\\c" + ZIELONY_ASS + "}" + w.upper() + "{\\c&H00FAF7F5&}") if poczatek + j == i
                         else w.upper() for j, (w, _, _) in enumerate(grupa))
        koniec = slowa_czasy[i + 1][1] if i + 1 < len(slowa_czasy) else do + 0.4
        linie.append(f"Dialogue: 0,{czas_ass(od)},{czas_ass(max(koniec, od + 0.1))},Slowa,{tekst}")
    cel.write_text("\n".join(linie) + "\n", encoding="utf-8")


def main() -> None:
    ap = argparse.ArgumentParser(description="C13 — shorts")
    ap.add_argument("--work", required=True, type=Path)
    ap.add_argument("--script", required=True, type=Path)
    ap.add_argument("--pakiet", required=True, type=Path)
    ap.add_argument("--srodek", type=float, default=0.5, help="poziomy środek kadru 9:16 (0–1)")
    ap.add_argument("--mem-max", default=proc.DOMYSLNY_LIMIT)
    a = ap.parse_args()

    cut = json.loads((a.work / "cut.json").read_text(encoding="utf-8"))
    slowa = json.loads((a.work / "transcript.json").read_text(encoding="utf-8"))["slowa"]
    zdania = {z["id"]: z for z in czytaj_scenariusz(a.script)}
    os_czasu = {o["id"]: o for o in cut["os_czasu"]}
    kolejnosc = [o["id"] for o in cut["os_czasu"]]
    zrodlo = next(a.work / n for n in ("kolor.mp4", "master.mp4") if (a.work / n).is_file())
    opisy = json.loads((a.pakiet / "shorts.json").read_text(encoding="utf-8"))
    katalog = a.work / "shorts"
    katalog.mkdir(exist_ok=True)

    for nr, s in enumerate(opisy, 1):
        if s["od"] not in os_czasu or s["do"] not in os_czasu:
            sys.exit(f"błąd: short {nr}: zdania {s['od']}–{s['do']} nie ma w montażu")
        ids = kolejnosc[kolejnosc.index(s["od"]):kolejnosc.index(s["do"]) + 1]
        start, koniec = os_czasu[s["od"]]["montaz_start"], os_czasu[s["do"]]["montaz_koniec"]
        if koniec - start > MAX_S:
            sys.exit(f"błąd: short {nr} trwa {koniec - start:.0f} s, limit {MAX_S:.0f} s")
        slowa_czasy = []
        for i in ids:
            if i in zdania:
                slowa_czasy += [(w, od - start, do - start) for w, (od, do)
                                in zip(zdania[i]["en"].split(), czasy_zdania(zdania[i], os_czasu[i], slowa))]
        ass = katalog / f"short-{nr}.ass"
        napisy_ass(slowa_czasy, ass)
        szer_wycinka = f"ih*{SZER}/{WYS}"
        filtr = (f"crop={szer_wycinka}:ih:(iw-{szer_wycinka})*{a.srodek}:0,scale={SZER}:{WYS}:flags=lanczos,"
                 f"subtitles={ass}:fontsdir={PROJEKT / 'assets' / 'fonts'},format=yuv420p")
        cel = katalog / f"short-{nr}.mp4"
        proc.run(["ffmpeg", "-nostdin", "-hide_banner", "-loglevel", "error", "-y", "-ss", f"{start:.3f}",
                  "-t", f"{koniec - start:.3f}", "-i", str(zrodlo), "-vf", filtr, "-af", "afade=t=out:st="
                  f"{max(0, koniec - start - 0.3):.3f}:d=0.3", "-c:v", "libx264", "-preset", "medium", "-crf", "20",
                  "-c:a", "aac", "-b:a", "192k", "-movflags", "+faststart", str(cel)],
                 mem_max=a.mem_max, opis=f"short {nr}")
        print(f"     short {nr}: {s['od']}–{s['do']}, {koniec - start:.1f} s → {cel.name}")
    print(f"OK: {len(opisy)} shorts w {katalog}")


if __name__ == "__main__":
    main()
