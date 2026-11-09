#!/usr/bin/env python3
"""G1 — runner: maszyna stanów filmów i zadania okresowe kanału.

Każdy film ma `content/pipeline/<slug>/status.json`. Jeden przebieg (`tick`, z timera co 15 min) przesuwa
każdy film o tyle kroków, ile się da bez czekania na człowieka, i wykonuje zadania okresowe. Kroki są
idempotentne: przerwany przebieg powtarza się w następnym. Błąd zatrzymuje tylko ten film, nie cały runner.

Przepływ (docs/PIPELINE.md §2):
    IDEA → SCRIPT_DRAFT → SCRIPT_REVIEW [✋] → READY_TO_RECORD → RECORDED → RENDERED → QC_PASS → PACKAGED
    → UPLOADED_PRIVATE → PREVIEW_REVIEW [✋] → SCHEDULED → PUBLISHED → SHORTS_SCHEDULED → ANALYZED

Polecenia:
    runner.py tick                                    jeden przebieg (timer)
    runner.py nowy <slug> [--zrodlo X] [--filar Y]    nowy film
    runner.py status                                  stan wszystkich filmów
    runner.py akceptuj|popraw <slug> [--uwagi "…"]    decyzja na bramce bez Discorda
    runner.py ustaw <slug> <STAN> [--yt-id ID]        ręczne przestawienie (np. po wgraniu w Studio)
    runner.py kalendarz                               odśwież content/calendar.md
"""

from __future__ import annotations

import argparse
import fcntl
import json
import re
import subprocess
import sys
import traceback
from datetime import date, datetime, timedelta
from pathlib import Path
from zoneinfo import ZoneInfo

sys.path.insert(0, str(Path(__file__).resolve().parent))
import agent  # noqa: E402
import discord  # noqa: E402

PROJEKT = Path(__file__).resolve().parent.parent
SKRYPTY = PROJEKT / "scripts"
PIPELINE = PROJEKT / "content" / "pipeline"
KONFIG = json.loads((PROJEKT / "config" / "kanal.json").read_text(encoding="utf-8"))
STREFA = ZoneInfo(KONFIG["strefa"])
INBOX = Path.home() / "inbox"
FILMY = Path.home() / "film"
STANY = ["IDEA", "SCRIPT_DRAFT", "SCRIPT_REVIEW", "READY_TO_RECORD", "RECORDED", "RENDERED", "QC_FAIL",
         "QC_PASS", "PACKAGED", "UPLOADED_PRIVATE", "PREVIEW_REVIEW", "SCHEDULED", "PUBLISHED",
         "SHORTS_SCHEDULED", "ANALYZED"]
MAX_PROB = 3
DNI = ["monday", "tuesday", "wednesday", "thursday", "friday", "saturday", "sunday"]


# ---------- stan ----------

def plik_stanu(slug: str) -> Path:
    return PIPELINE / slug / "status.json"


def wczytaj(slug: str) -> dict:
    p = plik_stanu(slug)
    if not p.is_file():
        sys.exit(f"błąd: nie ma filmu {slug} ({p})")
    return json.loads(p.read_text(encoding="utf-8"))


def zapisz(st: dict) -> None:
    p = plik_stanu(st["slug"])
    p.parent.mkdir(parents=True, exist_ok=True)
    tmp = p.with_suffix(".tmp")
    tmp.write_text(json.dumps(st, ensure_ascii=False, indent=2), encoding="utf-8")
    tmp.replace(p)          # zapis atomowy: przerwany przebieg nie zostawi połowy pliku


def przejdz(st: dict, stan: str, opis: str = "") -> None:
    st["historia"].append({"czas": datetime.now(STREFA).isoformat(timespec="seconds"),
                           "z": st["stan"], "do": stan, "opis": opis})
    st["stan"], st["blad"], st["proby"] = stan, None, 0
    zapisz(st)
    print(f"  {st['slug']}: → {stan}" + (f" ({opis})" if opis else ""))


def wszystkie() -> list[dict]:
    return [json.loads(p.read_text(encoding="utf-8")) for p in sorted(PIPELINE.glob("*/status.json"))]


def skrypt(*argumenty: str, limit_s: int = 7200) -> subprocess.CompletedProcess:
    return subprocess.run([sys.executable, *argumenty], cwd=PROJEKT, capture_output=True, text=True,
                          timeout=limit_s)


def dostepny(nazwa: str) -> bool:
    return (SKRYPTY / nazwa).is_file()


# ---------- ścieżki filmu ----------

def scenariusz(st: dict) -> Path:
    return PROJEKT / "content" / "scripts" / f"{st['slug']}.md"


def pakiet(st: dict) -> Path:
    return PROJEKT / "content" / "publish" / st["slug"]


def katalog(st: dict) -> Path:
    return FILMY / st["slug"]


def nagranie(st: dict) -> Path | None:
    """Plik z inboxu: `yt_<slug>*.mp4`, przy czym myślnik i podkreślnik w nazwie są równoważne."""
    przedrostek = f"yt_{st['slug']}".replace("-", "_")
    pasujace = [p for p in INBOX.glob("yt*.mp4") if p.name.lower().replace("-", "_").startswith(przedrostek)]
    return max(pasujace, key=lambda p: p.stat().st_mtime) if pasujace else None


def teleprompter(st: dict) -> Path:
    """Kolumna EN scenariusza, zdanie pod zdaniem — format, który czyta aplikacja w telefonie."""
    cel = scenariusz(st).with_suffix(".teleprompter.txt")
    if not cel.is_file():
        wiersze = re.findall(r"^\|\s*(L\d{3,})\s*\|([^|]*)\|", scenariusz(st).read_text(encoding="utf-8"), re.M)
        cel.write_text("\n\n".join(f"{i}  {t.strip()}" for i, t in wiersze if t.strip()) + "\n", encoding="utf-8")
    return cel


# ---------- kalendarz (A2) ----------

def sloty(od: datetime, ile: int) -> list[datetime]:
    """Kolejne terminy publikacji: stały dzień tygodnia i godzina z config/kanal.json."""
    godz, minuta = map(int, KONFIG["godzina_publikacji"].split(":"))
    dzien = DNI.index(KONFIG["dzien_publikacji"])
    t = od.astimezone(STREFA).replace(hour=godz, minute=minuta, second=0, microsecond=0)
    t += timedelta(days=(dzien - t.weekday()) % 7)
    if t <= od:
        t += timedelta(days=7)
    return [t + timedelta(weeks=i) for i in range(ile)]


def embargo(st: dict) -> date | None:
    if not scenariusz(st).is_file():
        return None
    m = re.search(r"^publish_after:\s*(\d{4}-\d{2}-\d{2})", scenariusz(st).read_text(encoding="utf-8"), re.M)
    return date.fromisoformat(m[1]) if m else None


def wolny_termin(st: dict) -> datetime:
    zajete = {f["publikacja"] for f in wszystkie() if f.get("publikacja") and f["slug"] != st["slug"]}
    granica = embargo(st)
    for t in sloty(datetime.now(STREFA), 104):
        if t.isoformat() not in zajete and (not granica or t.date() >= granica):
            return t
    raise RuntimeError("brak wolnego terminu w ciągu dwóch lat")


def kalendarz() -> Path:
    filmy = wszystkie()
    gotowe = [f for f in filmy if f["stan"] in ("QC_PASS", "PACKAGED", "UPLOADED_PRIVATE", "PREVIEW_REVIEW")]
    zaplanowane = sorted((f for f in filmy if f.get("publikacja")), key=lambda f: f["publikacja"])
    ostatnie = [f.get("filar") for f in zaplanowane if f.get("filar")][-len(KONFIG["filary"]) + 1:]
    kolejne = [f for f in KONFIG["filary"] if f not in ostatnie] + ostatnie
    linie = ["# Kalendarz redakcyjny", "",
             f"_Generowany przez `runner.py kalendarz` ({datetime.now(STREFA):%Y-%m-%d %H:%M}). "
             f"Rytm: 1 film/tydz. ({KONFIG['dzien_publikacji']} {KONFIG['godzina_publikacji']}), "
             f"bufor {KONFIG['bufor_filmow']} gotowych filmów._", "",
             f"**Bufor:** {len(gotowe)}/{KONFIG['bufor_filmow']} gotowych do publikacji"
             + (" — **za mało, nagraj kolejne**" if len(gotowe) < KONFIG["bufor_filmow"] else ""), "",
             "## Zaplanowane", "", "| Termin | Film | Filar | Stan |", "|---|---|---|---|"]
    linie += [f"| {f['publikacja'][:16].replace('T', ' ')} | {f['slug']} | {f.get('filar') or '—'} | {f['stan']} |"
              for f in zaplanowane] or ["| — | — | — | — |"]
    linie += ["", "## W produkcji", "", "| Film | Filar | Stan | Embargo |", "|---|---|---|---|"]
    linie += [f"| {f['slug']} | {f.get('filar') or '—'} | {f['stan']} | {embargo(f) or '—'} |"
              for f in filmy if not f.get("publikacja")] or ["| — | — | — | — |"]
    wolne = [t for t in sloty(datetime.now(STREFA), 8)
             if t.isoformat() not in {f.get("publikacja") for f in filmy}][:6]
    linie += ["", "## Wolne terminy i proponowany filar (rotacja)", "", "| Termin | Filar |", "|---|---|"]
    linie += [f"| {t:%Y-%m-%d %H:%M} | {kolejne[i % len(kolejne)]} |" for i, t in enumerate(wolne)]
    cel = PROJEKT / "content" / "calendar.md"
    cel.write_text("\n".join(linie) + "\n", encoding="utf-8")
    return cel


# ---------- bramki (G2) ----------

def bramka(st: dict, nazwa: str, tekst: str, pliki: list[Path] | None = None) -> str | None:
    """Prośba o decyzję wysyłana raz; zwraca 'akceptuj' / 'popraw' albo None, gdy decyzji jeszcze nie ma."""
    b = st.setdefault("bramki", {}).setdefault(nazwa, {})
    if b.get("decyzja"):                       # z linii poleceń albo z poprzedniego przebiegu
        return b["decyzja"]
    if "mid" not in b:
        b["mid"] = discord.popros_o_akceptacje(tekst, pliki)
        b["wyslano"] = datetime.now(STREFA).isoformat(timespec="seconds")
        zapisz(st)
        return None
    decyzja, uwagi = discord.decyzja(b["mid"])
    if decyzja:
        b["decyzja"], b["uwagi"] = decyzja, uwagi
        zapisz(st)
    return decyzja


def wyczysc_bramke(st: dict, nazwa: str) -> None:
    st.setdefault("bramki", {}).pop(nazwa, None)


def powiadom_raz(st: dict, klucz: str, tekst: str, pliki: list[Path] | None = None) -> None:
    wyslane = st.setdefault("powiadomienia", [])
    if klucz not in wyslane:
        discord.wyslij(tekst, pliki)
        wyslane.append(klucz)
        zapisz(st)


# ---------- kroki filmu ----------

def krok_idea(st: dict) -> None:
    if not scenariusz(st).is_file():
        ok, odp = agent.uruchom(f"/scenariusz {st['slug']} {st.get('zrodlo') or ''}".strip(), f"scenariusz-{st['slug']}")
        if not ok or not scenariusz(st).is_file():
            raise RuntimeError(f"agent nie napisał scenariusza: {odp[-300:]}")
    przejdz(st, "SCRIPT_DRAFT", "scenariusz jest")


def krok_szkic(st: dict) -> None:
    kontrola = skrypt("scripts/compliance.py", "--script", str(scenariusz(st)))
    if kontrola.returncode != 0:
        if st["proby"] >= 1:
            raise RuntimeError(f"kontrola zgodności nadal nie przechodzi:\n{kontrola.stdout[-800:]}")
        agent.uruchom(f"Popraw content/scripts/{st['slug']}.md tak, aby `python3 scripts/compliance.py --script "
                      f"content/scripts/{st['slug']}.md` nie zgłaszało błędów. Błędy:\n{kontrola.stdout}",
                      f"poprawka-{st['slug']}")
        st["proby"] += 1
        zapisz(st)
        return
    teleprompter(st)
    wyczysc_bramke(st, "scenariusz")
    st["uwagi_zgodnosci"] = kontrola.stdout.strip()
    przejdz(st, "SCRIPT_REVIEW", "kontrola zgodności przeszła")


def krok_przeglad_scenariusza(st: dict) -> None:
    decyzja = bramka(st, "scenariusz",
                     f"**Scenariusz do akceptacji: {st['slug']}**\n`content/scripts/{st['slug']}.md`\n"
                     f"{st.get('uwagi_zgodnosci', '')}", [scenariusz(st)])
    if decyzja == "akceptuj":
        przejdz(st, "READY_TO_RECORD", "scenariusz zaakceptowany")
    elif decyzja == "popraw":
        uwagi = st["bramki"]["scenariusz"].get("uwagi") or "brak treści uwag"
        agent.uruchom(f"/scenariusz {st['slug']} — popraw istniejący scenariusz według uwag właściciela:\n{uwagi}",
                      f"uwagi-{st['slug']}")
        wyczysc_bramke(st, "scenariusz")
        przejdz(st, "SCRIPT_DRAFT", "poprawki według uwag")


def krok_do_nagrania(st: dict) -> None:
    plik = nagranie(st)
    if plik:
        st["wideo"] = str(plik)
        przejdz(st, "RECORDED", plik.name)
        return
    powiadom_raz(st, "do-nagrania",
                 f"**Do nagrania: {st['slug']}**\nTeleprompter: `{teleprompter(st).relative_to(PROJEKT)}`\n"
                 f"Standard: `docs/RECORDING.md`. Nazwa pliku: `yt_{st['slug']}.mp4`.", [teleprompter(st)])


def montaz(filmy: list[dict]) -> None:
    """B4: wszystkie nagrane filmy w jednym uruchomieniu workera (jedna opłacona godzina)."""
    argumenty = ["scripts/worker.py", "job", "--work", str(FILMY / "_przebieg")]
    for st in filmy:
        dane = scenariusz(st).with_suffix(".dane.json")
        argumenty += ["--film", st["wideo"], str(scenariusz(st)), *([str(dane)] if dane.is_file() else [])]
        if st.get("kolor"):
            argumenty += ["--kolor", st["kolor"]]
    print(f"  montaż na workerze: {', '.join(f['slug'] for f in filmy)}")
    wynik = skrypt(*argumenty, limit_s=4 * 3600)
    (PIPELINE / "_ostatni-montaz.log").write_text(wynik.stdout[-20000:] + wynik.stderr[-5000:], encoding="utf-8")
    przebieg = FILMY / "_przebieg"
    for st in filmy:
        zrodlo = przebieg / st["slug"] if len(filmy) > 1 else przebieg
        if zrodlo.is_dir() and (zrodlo / "final.mp4").is_file():
            katalog(st).parent.mkdir(parents=True, exist_ok=True)
            if katalog(st).exists():
                katalog(st).rename(katalog(st).with_name(f"{st['slug']}-{datetime.now():%Y%m%d%H%M}"))
            zrodlo.rename(katalog(st))
            przejdz(st, "RENDERED", "montaż na workerze")
        else:
            st["proby"] += 1
            st["blad"] = f"montaż nie powiódł się (próba {st['proby']}), log: content/pipeline/_ostatni-montaz.log"
            zapisz(st)
    if len(filmy) > 1 and przebieg.is_dir() and not any(przebieg.iterdir()):
        przebieg.rmdir()


def krok_wyrenderowany(st: dict) -> None:
    qc = json.loads((katalog(st) / "qc.json").read_text(encoding="utf-8"))
    pliki = [katalog(st) / "qc-klatki.jpg", katalog(st) / "kolor-podglad.jpg"]
    if qc["werdykt"] == "FAIL":
        przejdz(st, "QC_FAIL", "; ".join(qc["bledy"])[:300])
        discord.wyslij(f"**QC FAIL: {st['slug']}**\n" + "\n".join(f"- {b}" for b in qc["bledy"]), pliki)
        return
    discord.wyslij(f"**Montaż gotowy: {st['slug']}** ({qc['werdykt']}, {qc['dlugosc_s'] / 60:.1f} min, "
                   f"{qc['lufs']} LUFS)" + "".join(f"\n- {u}" for u in qc["uwagi"]), pliki)
    przejdz(st, "QC_PASS", qc["werdykt"])


def krok_qc_pass(st: dict) -> None:
    if not (pakiet(st) / "description.txt").is_file():
        ok, odp = agent.uruchom(f"/publikacja {st['slug']}", f"publikacja-{st['slug']}")
        if not ok or not (pakiet(st) / "description.txt").is_file():
            raise RuntimeError(f"agent nie przygotował pakietu: {odp[-300:]}")
    kontrola = skrypt("scripts/compliance.py", "--script", str(scenariusz(st)), "--pakiet", str(pakiet(st)))
    if kontrola.returncode != 0:
        raise RuntimeError(f"pakiet nie przechodzi kontroli zgodności:\n{kontrola.stdout[-800:]}")
    if dostepny("shorts.py") and (pakiet(st) / "shorts.json").is_file():
        s = skrypt("scripts/shorts.py", "--work", str(katalog(st)), "--script", str(scenariusz(st)),
                   "--pakiet", str(pakiet(st)))
        if s.returncode != 0:
            raise RuntimeError(f"shorts: {s.stdout[-300:]}{s.stderr[-300:]}")
    przejdz(st, "PACKAGED", "pakiet i shorts")


def youtube_gotowy() -> bool:
    return dostepny("upload.py") and skrypt("scripts/upload.py", "sprawdz").returncode == 0


def krok_pakiet(st: dict) -> None:
    if st.get("yt_id"):
        przejdz(st, "UPLOADED_PRIVATE", st["yt_id"])
        return
    if not youtube_gotowy():
        powiadom_raz(st, "wgraj-recznie",
                     f"**Gotowe do wgrania: {st['slug']}** (brak autoryzacji YouTube API)\n"
                     f"Plik: `{katalog(st) / 'final.mp4'}`, pakiet: `content/publish/{st['slug']}/`.\n"
                     f"Po wgraniu jako prywatny: `runner.py ustaw {st['slug']} UPLOADED_PRIVATE --yt-id <ID>`")
        return
    wynik = skrypt("scripts/upload.py", "film", "--work", str(katalog(st)), "--pakiet", str(pakiet(st)),
                   "--filar", st.get("filar") or "")
    m = re.search(r"YT_ID=(\S+)", wynik.stdout)
    if wynik.returncode != 0 or not m:
        raise RuntimeError(f"upload: {wynik.stdout[-400:]}{wynik.stderr[-400:]}")
    st["yt_id"] = m[1]
    przejdz(st, "UPLOADED_PRIVATE", st["yt_id"])


def krok_prywatny(st: dict) -> None:
    lista = pakiet(st) / "checklist.md"
    discord.wyslij(f"**Lista ręczna w Studio (D5): {st['slug']}**\nhttps://studio.youtube.com/video/{st['yt_id']}/edit\n"
                   f"Plansza końcowa, karty, przypięty komentarz, Test & Compare — szczegóły w załączniku.",
                   [lista] if lista.is_file() else None)
    wyczysc_bramke(st, "podglad")
    przejdz(st, "PREVIEW_REVIEW", "lista ręczna wysłana")


def krok_podglad(st: dict) -> None:
    decyzja = bramka(st, "podglad", f"**Podgląd prywatny do akceptacji: {st['slug']}**\n"
                                    f"https://youtu.be/{st['yt_id']}\nPo akceptacji film dostanie najbliższy wolny termin.")
    if decyzja == "akceptuj":
        termin = wolny_termin(st)
        if youtube_gotowy():
            wynik = skrypt("scripts/upload.py", "zaplanuj", st["yt_id"], termin.isoformat())
            if wynik.returncode != 0:
                raise RuntimeError(f"planowanie: {wynik.stdout[-300:]}{wynik.stderr[-300:]}")
        else:
            discord.wyslij(f"Ustaw publikację {st['slug']} w Studio na **{termin:%Y-%m-%d %H:%M}** ({KONFIG['strefa']}).")
        st["publikacja"] = termin.isoformat()
        przejdz(st, "SCHEDULED", f"{termin:%Y-%m-%d %H:%M}")
    elif decyzja == "popraw":
        powiadom_raz(st, f"popraw-podglad-{st['bramki']['podglad'].get('mid')}",
                     f"Uwagi do {st['slug']} zapisane. Po poprawkach: `runner.py ustaw {st['slug']} QC_PASS`.")


def krok_zaplanowany(st: dict) -> None:
    if datetime.now(STREFA) >= datetime.fromisoformat(st["publikacja"]):
        przejdz(st, "PUBLISHED", "termin minął")


def krok_opublikowany(st: dict) -> None:
    shorts = sorted((katalog(st) / "shorts").glob("*.mp4")) if (katalog(st) / "shorts").is_dir() else []
    if shorts and youtube_gotowy():
        start = datetime.fromisoformat(st["publikacja"])
        for i, s in enumerate(shorts, 1):
            termin = start + timedelta(days=KONFIG["shorts_co_dni"] * i)
            wynik = skrypt("scripts/upload.py", "short", "--plik", str(s), "--pakiet", str(pakiet(st)),
                           "--film", st["yt_id"], "--termin", termin.isoformat())
            if wynik.returncode != 0:
                raise RuntimeError(f"short {s.name}: {wynik.stdout[-300:]}{wynik.stderr[-300:]}")
    elif shorts:
        powiadom_raz(st, "shorts-recznie", f"Shorts {st['slug']} do wgrania ręcznie: `{katalog(st) / 'shorts'}`")
    przejdz(st, "SHORTS_SCHEDULED", f"{len(shorts)} shorts")


def krok_analityka(st: dict) -> None:
    zrobione = st.setdefault("analityka", [])
    start = datetime.fromisoformat(st["publikacja"])
    for dni in KONFIG["analityka_po_dniach"]:
        if dni in zrobione or datetime.now(STREFA) < start + timedelta(days=dni):
            continue
        if not (dostepny("analytics.py") and youtube_gotowy()):
            return
        wynik = skrypt("scripts/analytics.py", "raport", st["yt_id"], "--slug", st["slug"], "--dni", str(dni))
        if wynik.returncode != 0:
            raise RuntimeError(f"analityka: {wynik.stdout[-300:]}{wynik.stderr[-300:]}")
        raport = PROJEKT / "content" / "analytics" / f"{st['slug']}-{dni}d.md"
        discord.wyslij(f"**Analityka {dni} dni: {st['slug']}**", [raport])
        zrobione.append(dni)
        zapisz(st)
    if all(d in zrobione for d in KONFIG["analityka_po_dniach"]):
        przejdz(st, "ANALYZED", "raporty 7/28 dni")


KROKI = {"IDEA": krok_idea, "SCRIPT_DRAFT": krok_szkic, "SCRIPT_REVIEW": krok_przeglad_scenariusza,
         "READY_TO_RECORD": krok_do_nagrania, "RENDERED": krok_wyrenderowany, "QC_PASS": krok_qc_pass,
         "PACKAGED": krok_pakiet, "UPLOADED_PRIVATE": krok_prywatny, "PREVIEW_REVIEW": krok_podglad,
         "SCHEDULED": krok_zaplanowany, "PUBLISHED": krok_opublikowany, "SHORTS_SCHEDULED": krok_analityka}


# ---------- zadania okresowe ----------

OKRESOWE = PIPELINE / "_okresowe.json"


def zadania_okresowe() -> None:
    ostatnio = json.loads(OKRESOWE.read_text(encoding="utf-8")) if OKRESOWE.is_file() else {}
    dzis = datetime.now(STREFA).date()
    tydzien, miesiac = f"{dzis:%G-W%V}", f"{dzis:%Y-%m}"
    zadania = [  # (klucz, okres, opis, polecenie)
        ("kontekst", str(dzis), "synchronizacja kontekstu (A1)", lambda: skrypt("scripts/sync_context.py")),
        ("retencja", str(dzis), "retencja i dysk (G4)",
         lambda: skrypt("scripts/retencja.py") if dostepny("retencja.py") else None),
        ("komentarze", str(dzis), "przegląd komentarzy (E2)",
         lambda: skrypt("scripts/komentarze.py") if dostepny("komentarze.py") and youtube_gotowy() else None),
        ("pomysly", tydzien, "pomysły tygodnia (A3)", lambda: agent.uruchom("/pomysly", "pomysly")),
        ("kalendarz", tydzien, "kalendarz i bufor (A2)", sprawdz_bufor),
        ("newsletter", miesiac, "szkic newslettera (E3)",
         lambda: skrypt("scripts/newsletter.py") if dostepny("newsletter.py") else None),
    ]
    for klucz, okres, opis, polecenie in zadania:
        if ostatnio.get(klucz) == okres:
            continue
        print(f"  okresowe: {opis}")
        try:
            wynik = polecenie()
            if isinstance(wynik, subprocess.CompletedProcess) and wynik.returncode != 0:
                discord.wyslij(f"Zadanie okresowe „{opis}” nie powiodło się:\n{(wynik.stdout + wynik.stderr)[-600:]}")
            elif isinstance(wynik, tuple) and not wynik[0]:
                discord.wyslij(f"Zadanie okresowe „{opis}” nie powiodło się:\n{wynik[1][-600:]}")
            elif klucz == "pomysly":
                najnowszy = max((PROJEKT / "content" / "ideas").glob("*.md"), key=lambda p: p.stat().st_mtime)
                discord.wyslij(f"**Pomysły na ten tydzień** — wybierz: `runner.py nowy <slug> --zrodlo …`", [najnowszy])
        except Exception as e:  # noqa: BLE001 — zadanie okresowe nie może zatrzymać produkcji filmów
            discord.wyslij(f"Zadanie okresowe „{opis}”: {e}")
        ostatnio[klucz] = okres
    OKRESOWE.parent.mkdir(parents=True, exist_ok=True)
    OKRESOWE.write_text(json.dumps(ostatnio, indent=2), encoding="utf-8")


def sprawdz_bufor() -> None:
    cel = kalendarz()
    gotowe = [f for f in wszystkie() if f["stan"] in ("QC_PASS", "PACKAGED", "UPLOADED_PRIVATE", "PREVIEW_REVIEW")]
    if len(gotowe) < KONFIG["bufor_filmow"]:
        do_nagrania = [f["slug"] for f in wszystkie() if f["stan"] == "READY_TO_RECORD"]
        discord.wyslij(f"Bufor: {len(gotowe)}/{KONFIG['bufor_filmow']} gotowych filmów. "
                       + (f"Sesja nagraniowa (B4): {', '.join(do_nagrania)}." if do_nagrania
                          else "Brak zaakceptowanych scenariuszy — wybierz temat z pomysłów."), [cel])


# ---------- przebieg ----------

def tick(okresowe: bool = True, commit: bool = True) -> None:
    PIPELINE.mkdir(parents=True, exist_ok=True)
    with (PIPELINE / ".runner.lock").open("w") as blokada:
        try:
            fcntl.flock(blokada, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError:
            print("runner już działa (np. trwa montaż) — pomijam ten przebieg")
            return
        for st in wszystkie():
            for _ in range(len(STANY)):       # film idzie dalej, dopóki krok nie musi czekać
                stan = st["stan"]
                if stan not in KROKI or (st.get("blad") and st["proby"] >= MAX_PROB):
                    break
                try:
                    KROKI[stan](st)
                except Exception as e:  # noqa: BLE001 — błąd jednego filmu nie zatrzymuje pozostałych
                    st["proby"] = st.get("proby", 0) + 1
                    st["blad"] = f"{type(e).__name__}: {e}"[:1500]
                    zapisz(st)
                    traceback.print_exc()
                    if st["proby"] >= MAX_PROB:
                        discord.wyslij(f"**{st['slug']} zatrzymany na {stan}** po {MAX_PROB} próbach:\n{st['blad'][:900]}\n"
                                       f"Po naprawie: `runner.py ustaw {st['slug']} {stan}`")
                    break
                st = wczytaj(st["slug"])
                if st["stan"] == stan:
                    break
        nagrane = [st for st in wszystkie() if st["stan"] == "RECORDED" and st.get("proby", 0) < MAX_PROB]
        if nagrane:
            montaz(nagrane)
            for st in wszystkie():
                if st["stan"] == "RENDERED":
                    try:
                        krok_wyrenderowany(st)
                    except Exception as e:  # noqa: BLE001
                        st["blad"] = str(e)
                        zapisz(st)
        if okresowe:
            zadania_okresowe()
        if commit:
            zatwierdz_zmiany()


def zatwierdz_zmiany() -> None:
    """Stan filmów i treści od agentów trafiają do repo osobnym commitem, jak przy synchronizacji kontekstu."""
    if subprocess.run(["git", "status", "--porcelain", "content"], cwd=PROJEKT, capture_output=True,
                      text=True).stdout.strip():
        subprocess.run(["git", "add", "content"], cwd=PROJEKT, check=True)
        subprocess.run(["git", "commit", "-q", "-m", f"pipeline: przebieg runnera {datetime.now(STREFA):%Y-%m-%d %H:%M}"],
                       cwd=PROJEKT, check=False)


# ---------- linia poleceń ----------

def main() -> None:
    ap = argparse.ArgumentParser(description="G1 — runner pipeline'u")
    pod = ap.add_subparsers(dest="cmd", required=True)
    p = pod.add_parser("tick")
    p.add_argument("--bez-okresowych", action="store_true", help="tylko filmy (testy)")
    p.add_argument("--bez-commita", action="store_true")
    pod.add_parser("status")
    pod.add_parser("kalendarz")
    p = pod.add_parser("nowy")
    p.add_argument("slug")
    p.add_argument("--zrodlo", default="")
    p.add_argument("--filar", choices=KONFIG["filary"])
    for nazwa in ("akceptuj", "popraw"):
        p = pod.add_parser(nazwa)
        p.add_argument("slug")
        p.add_argument("--uwagi", default="")
    p = pod.add_parser("ustaw")
    p.add_argument("slug")
    p.add_argument("stan", choices=STANY)
    p.add_argument("--yt-id")
    p.add_argument("--kolor", choices=["czysty", "kinowy", "pastelowy"])
    a = ap.parse_args()

    if a.cmd == "tick":
        tick(not a.bez_okresowych, not a.bez_commita)
    elif a.cmd == "kalendarz":
        print(kalendarz())
    elif a.cmd == "status":
        for st in wszystkie():
            print(f"{st['slug']:40} {st['stan']:18} {st.get('publikacja', '')[:16]:16} {st.get('blad') or ''}"[:200])
    elif a.cmd == "nowy":
        if not re.fullmatch(r"[a-z0-9][a-z0-9-]*", a.slug):
            sys.exit("błąd: slug to małe litery, cyfry i myślniki")
        if plik_stanu(a.slug).is_file():
            sys.exit(f"błąd: film {a.slug} już istnieje")
        st = {"slug": a.slug, "stan": "IDEA", "zrodlo": a.zrodlo, "filar": a.filar, "historia": [],
              "blad": None, "proby": 0}
        zapisz(st)
        print(f"OK: {plik_stanu(a.slug)}")
    elif a.cmd in ("akceptuj", "popraw"):
        st = wczytaj(a.slug)
        nazwa = {"SCRIPT_REVIEW": "scenariusz", "PREVIEW_REVIEW": "podglad"}.get(st["stan"])
        if not nazwa:
            sys.exit(f"błąd: {a.slug} jest w stanie {st['stan']}, nie czeka na decyzję")
        st.setdefault("bramki", {}).setdefault(nazwa, {}).update({"decyzja": a.cmd, "uwagi": a.uwagi})
        zapisz(st)
        print(f"OK: {a.cmd} ({nazwa}); zadziała w najbliższym przebiegu")
    elif a.cmd == "ustaw":
        st = wczytaj(a.slug)
        if a.yt_id:
            st["yt_id"] = a.yt_id
        if a.kolor:
            st["kolor"] = a.kolor
        przejdz(st, a.stan, "ręcznie")


if __name__ == "__main__":
    main()
