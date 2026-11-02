#!/usr/bin/env python3
"""C5 — dźwięk: filtr górnoprzepustowy, odszumianie, kompresja, −14 LUFS, opcjonalna muzyka z duckingiem.

Przy nagraniu w pokoju dźwięk jest największą dźwignią jakości (docs/PIPELINE.md §5), a jednocześnie
najłatwiejszą do zautomatyzowania. Łańcuch:

1. `highpass` 80 Hz — usuwa dudnienie biurka, klimatyzacji i pomruk pomieszczenia,
2. `afftdn` — odszumianie widmowe (szum krzesła, wentylatora),
3. `acompressor` — wyrównanie głośności zdań mówionych z różną energią,
4. pomiar `loudnorm`, stałe podbicie `volume` i limiter `alimiter` — razem dają −14 LUFS / −1,5 dBTP
   (poziom, do którego YouTube nie dotyka nagrania). Samo `loudnorm:linear=true` tu nie wystarcza:
   przycina podbicie tak, żeby nie przekroczyć szczytu, więc przy mowie z małą dynamiką zatrzymuje się
   kilka LU poniżej celu (test 2026-11-02: −16,7 zamiast −14,0, przy szczycie −0,97 ponad limitem).
   Limiter zdejmuje pojedyncze szczyty i pozwala dojść do celu,
5. muzyka (`--music`) ściszana pod głosem przez `sidechaincompress` — ducking, nie stała głośność.

    python3 scripts/audio_master.py --work /tmp/film-01 --in cut.mp4
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import proc  # noqa: E402  — wspólny limiter pamięci

CEL_LUFS = -14.0
CEL_TP = -1.5
CEL_LRA = 11.0
# limiter pracuje na szczycie próbki, a cel jest w szczycie prawdziwym (między próbkami bywa głośniej);
# zapas 0,5 dB okazał się za mały (wyszło −1,44 przy limicie −1,5), więc schodzimy o cały decybel
ZAPAS_TP = 1.0
TOLERANCJA_LU = 0.3   # bliżej celu niż to i tak nikt nie usłyszy

MOWA = "highpass=f=80,afftdn=nf=-25,acompressor=threshold=-18dB:ratio=3:attack=5:release=120:makeup=2"
# Kompresor ma stały próg, więc materiał musi do niego wejść na sensownym poziomie. Nagranie telefonem
# z odległości potrafi mieć −27 LUFS (test 2026-11-02) — wtedy sygnał w ogóle nie przekracza progu,
# kompresja nie działa, odstęp szczytu od średniej zostaje duży i limiter zjada całe podbicie.
POZIOM_ROBOCZY = -16.0


def ffmpeg(args: list[str], mem: str, opis: str = "ffmpeg"):
    return proc.run(["ffmpeg", "-nostdin", "-hide_banner", *args], mem_max=mem, opis=opis)


def lancuch(music: Path | None, koncowka: str, wstepne: float = 0.0) -> str:
    """Graf filtrów: sama mowa albo mowa + podkład ściszany pod głosem; `koncowka` to pomiar albo poziom."""
    mowa = f"volume={wstepne:.2f}dB,{MOWA}" if wstepne else MOWA
    if not music:
        return f"[0:a]{mowa},{koncowka}[out]"
    return (f"[0:a]{mowa}[sp];"
            f"[1:a]volume=0.18[mus];"
            # kluczem jest mowa: gdy mówisz, muzyka schodzi; gdy milkniesz, wraca
            f"[mus][sp]sidechaincompress=threshold=0.03:ratio=8:attack=20:release=400[duck];"
            f"[sp][duck]amix=inputs=2:normalize=0,{koncowka}[out]")


def poziom(zmierzone_i: float, korekta: float = 0.0, zapas: float = ZAPAS_TP) -> str:
    """Podbicie do celu + limiter szczytów. `korekta` dociąga poziom, `zapas` odsuwa limiter od celu."""
    limit = 10 ** ((CEL_TP - zapas) / 20)
    return (f"volume={CEL_LUFS - zmierzone_i + korekta:.2f}dB,"
            f"alimiter=limit={limit:.4f}:attack=5:release=50:level=false")


def zmierz(src: Path, music: Path | None, mem: str, wstepne: float = 0.0, surowo: bool = False) -> dict:
    """Pomiar głośności: `surowo` = sam plik, bez filtrów (żeby ustawić wejście kompresora)."""
    analiza = f"loudnorm=I={CEL_LUFS}:TP={CEL_TP}:LRA={CEL_LRA}:print_format=json"
    graf = f"[0:a]{analiza}[out]" if surowo else lancuch(music, analiza, wstepne)
    args = ["-i", str(src)] + (["-i", str(music)] if music and not surowo else [])
    res = ffmpeg([*args, "-filter_complex", graf, "-map", "[out]", "-f", "null", "-"],
                 mem, "pomiar głośności")
    start = res.stderr.rfind("{")
    if start == -1:
        sys.exit("błąd: loudnorm nie zwrócił pomiaru — sprawdź, czy plik ma ścieżkę dźwiękową")
    return json.loads(res.stderr[start:res.stderr.rfind("}") + 1])


def main() -> None:
    ap = argparse.ArgumentParser(description="C5 — mastering dźwięku")
    ap.add_argument("--work", required=True, type=Path, help="katalog roboczy filmu")
    ap.add_argument("--in", dest="src", default="cut.mp4", help="plik wejściowy w katalogu roboczym")
    ap.add_argument("--music", type=Path, help="podkład muzyczny (opcjonalnie)")
    ap.add_argument("--out", default="master.mp4", help="nazwa wyniku w katalogu roboczym")
    ap.add_argument("--mem-max", default=proc.DOMYSLNY_LIMIT,
                    help="limit pamięci na krok FFmpeg (0 = bez limitu, np. na workerze)")
    a = ap.parse_args()

    src = a.src if Path(a.src).is_absolute() else a.work / a.src
    if not Path(src).is_file():
        sys.exit(f"błąd: nie ma pliku {src} — najpierw uruchom cut.py")
    if a.music and not a.music.is_file():
        sys.exit(f"błąd: nie ma podkładu {a.music}")

    surowe = zmierz(Path(src), None, a.mem_max, surowo=True)
    wstepne = POZIOM_ROBOCZY - float(surowe["input_i"])
    print(f"     wejście {surowe['input_i']} LUFS → podbicie {wstepne:+.1f} dB przed kompresorem")
    pomiar = zmierz(Path(src), a.music, a.mem_max, wstepne)
    wyjscie = a.work / a.out
    args = ["-y", "-i", str(src)] + (["-i", str(a.music)] if a.music else [])

    # Limiter zdejmuje część podbicia, a ile — zależy od materiału. Zamiast zgadywać: zmierz wynik
    # i jeśli odstaje od celu, policz jeszcze raz z poprawką. Jeden nawrót wystarcza w praktyce.
    korekta, zapas = 0.0, ZAPAS_TP
    for podejscie in range(4):
        ffmpeg([*args, "-filter_complex",
                lancuch(a.music, poziom(float(pomiar["input_i"]), korekta, zapas), wstepne),
                "-map", "0:v?", "-map", "[out]", "-c:v", "copy",
                "-c:a", "aac", "-b:a", "192k", "-ar", "48000", str(wyjscie)], a.mem_max, "mastering")
        kontrola = zmierz(wyjscie, None, a.mem_max, surowo=True)
        roznica = CEL_LUFS - float(kontrola["input_i"])
        nadmiar = float(kontrola["input_tp"]) - CEL_TP
        if podejscie == 3:
            break
        # Szczyt ma pierwszeństwo: limiter pilnuje próbek, ale koder AAC dokłada swoje przestrzelenia
        # (test 2026-11-02: limiter na −2,5 dB, a w gotowym pliku −1,17 dBTP), więc odsuwamy go dalej.
        if nadmiar > 0:
            zapas += nadmiar + 0.2
            print(f"     szczyt {kontrola['input_tp']} dBTP ponad limitem — limiter niżej o {nadmiar + 0.2:.2f} dB")
            continue
        if abs(roznica) <= TOLERANCJA_LU:
            break
        korekta += roznica
        print(f"     poprawka poziomu {roznica:+.2f} LU — kolejne podejście")
    # szczyt ponad limitem to błąd (YouTube dołoży swoje), poziom poniżej celu to tylko cichszy film
    szczyt_ok = float(kontrola["input_tp"]) <= CEL_TP
    uwagi = [] if szczyt_ok else [f"szczyt {kontrola['input_tp']} dBTP ponad limitem {CEL_TP}"]
    if abs(roznica) > TOLERANCJA_LU:
        uwagi.append(f"nie doszło do celu o {roznica:.2f} LU — materiał ma za duży odstęp "
                     f"szczytu od średniej, mocniejsze dociskanie słychać jako zniekształcenie")

    raport = {"wejscie": str(src), "podklad": str(a.music) if a.music else None,
              "przed": {"I": surowe["input_i"], "TP": surowe["input_tp"], "LRA": surowe["input_lra"]},
              "podbicie_przed_kompresorem_db": round(wstepne, 2),
              "po": {"I": kontrola["input_i"], "TP": kontrola["input_tp"], "LRA": kontrola["input_lra"]},
              "cel": {"I": CEL_LUFS, "TP": CEL_TP, "LRA": CEL_LRA}, "uwagi": uwagi}
    (a.work / "audio-raport.json").write_text(json.dumps(raport, ensure_ascii=False, indent=2), encoding="utf-8")

    print(f"{'OK' if szczyt_ok else 'UWAGA'}: {surowe['input_i']} → {kontrola['input_i']} LUFS "
          f"(cel {CEL_LUFS}), szczyt {kontrola['input_tp']} dBTP")
    for u in uwagi:
        print(f"     uwaga: {u}")
    print(f"     {wyjscie} + {a.work / 'audio-raport.json'}")


if __name__ == "__main__":
    main()
