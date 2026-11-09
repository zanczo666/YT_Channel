#!/usr/bin/env python3
"""D3 + F5 — wgrywanie przez YouTube Data API: film prywatnie, miniatura, napisy EN/PL, lokalizacja PL,
playlista filaru; planowanie publikacji; shorts; playlisty filarów.

Metadane bierze z `content/publish/<slug>/metadata.json` (pisze je agent `yt-producer`):
    {"title": "…", "description_file": "description.txt", "tags_file": "tags.txt",
     "thumbnail": "thumbnail-a.jpg", "pl": {"title": "…", "description": "…"}}

Uwaga (D4): projekt Google Cloud bez audytu API może wgrywać tylko filmy **prywatne** — planowanie
publikacji zadziała dopiero po audycie. Do tego czasu runner prosi o ustawienie terminu w Studio.

    python3 scripts/upload.py sprawdz
    python3 scripts/upload.py film --work ~/film/<slug> --pakiet content/publish/<slug> --filar "<filar>"
    python3 scripts/upload.py zaplanuj <video_id> <ISO 8601>
    python3 scripts/upload.py short --plik <mp4> --pakiet <katalog> --film <video_id> --termin <ISO>
    python3 scripts/upload.py playlisty
Każde polecenie przyjmuje `--na-sucho`: wypisuje zapytania zamiast je wysyłać.
"""

from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import yt_api  # noqa: E402
from yt_api import API, UPLOAD, BladApi, zapytanie  # noqa: E402

KONFIG = json.loads((Path(__file__).resolve().parent.parent / "config" / "kanal.json").read_text(encoding="utf-8"))
KAWALEK = 16 * 1024 * 1024
LIMIT_TYTULU, LIMIT_OPISU = 100, 5000
NA_SUCHO = False


def wyslij(metoda: str, url: str, **kw):
    if NA_SUCHO:
        cialo = kw.get("cialo")
        opis = json.dumps(cialo, ensure_ascii=False)[:400] if isinstance(cialo, dict) else f"{len(cialo or b'')} B"
        print(f"[na sucho] {metoda} {url.split('?')[0]} {kw.get('parametry', '')} {opis}")
        return {"id": "NA_SUCHO", "items": []}
    return zapytanie(metoda, url, **kw)


def metadane(pakiet: Path) -> dict:
    plik = pakiet / "metadata.json"
    if not plik.is_file():
        raise BladApi(f"brak {plik} — pakiet musi mieć metadata.json (agent yt-producer)")
    m = json.loads(plik.read_text(encoding="utf-8"))
    opis = (pakiet / m.get("description_file", "description.txt")).read_text(encoding="utf-8").strip()
    tagi_plik = pakiet / m.get("tags_file", "tags.txt")
    tagi = [t.strip() for t in tagi_plik.read_text(encoding="utf-8").splitlines() if t.strip()] if tagi_plik.is_file() else []
    if len(m["title"]) > LIMIT_TYTULU or len(opis) > LIMIT_OPISU:
        raise BladApi("tytuł ponad 100 znaków albo opis ponad 5000 znaków")
    return {**m, "description": opis, "tags": tagi}


def wgraj_plik(sciezka: Path, zasob: dict, czesci: str) -> str:
    """Wysyłanie wznawialne: najpierw sesja, potem plik kawałkami (przerwane łącze nie zaczyna od zera)."""
    rozmiar = sciezka.stat().st_size
    if NA_SUCHO:
        wyslij("POST", f"{UPLOAD}/videos", parametry={"part": czesci}, cialo=zasob)
        return "NA_SUCHO"
    odp = zapytanie("POST", f"{UPLOAD}/videos", {"uploadType": "resumable", "part": czesci}, zasob,
                    naglowki={"X-Upload-Content-Type": "video/mp4", "X-Upload-Content-Length": str(rozmiar)},
                    surowa=True)
    sesja = odp.headers["Location"]
    with sciezka.open("rb") as f:
        poz = 0
        while poz < rozmiar:
            f.seek(poz)
            dane = f.read(KAWALEK)
            r = zapytanie("PUT", sesja, cialo=dane, typ="video/mp4", surowa=True, naglowki={
                "Content-Range": f"bytes {poz}-{poz + len(dane) - 1}/{rozmiar}"})
            if r.status in (200, 201):
                return json.loads(r.read())["id"]
            zakres = r.headers.get("Range")                     # 308: serwer mówi, ile już ma
            poz = int(zakres.split("-")[1]) + 1 if zakres else poz
            print(f"  wysłano {poz / rozmiar:.0%}")
    raise BladApi("wysyłanie skończyło się bez identyfikatora filmu")


def multipart(metadane_json: dict, plik: Path, typ: str) -> tuple[bytes, str]:
    granica = "ytgranica7f3a"
    cialo = (f"--{granica}\r\nContent-Type: application/json; charset=UTF-8\r\n\r\n{json.dumps(metadane_json)}\r\n"
             f"--{granica}\r\nContent-Type: {typ}\r\n\r\n").encode() + plik.read_bytes() + f"\r\n--{granica}--\r\n".encode()
    return cialo, f"multipart/related; boundary={granica}"


def playlista(nazwa: str, utworz: bool = True) -> str | None:
    istniejace = wyslij("GET", f"{API}/playlists", parametry={"part": "snippet", "mine": "true", "maxResults": 50})
    for p in istniejace.get("items", []):
        if p["snippet"]["title"] == nazwa:
            return p["id"]
    if not utworz:
        return None
    nowa = wyslij("POST", f"{API}/playlists", parametry={"part": "snippet,status"}, cialo={
        "snippet": {"title": nazwa, "defaultLanguage": KONFIG["jezyk"]}, "status": {"privacyStatus": "public"}})
    return nowa["id"]


def film(a: argparse.Namespace) -> None:
    m = metadane(a.pakiet)
    zasob = {
        "snippet": {"title": m["title"], "description": m["description"], "tags": m["tags"],
                    "categoryId": KONFIG["kategoria_youtube"], "defaultLanguage": KONFIG["jezyk"],
                    "defaultAudioLanguage": KONFIG["jezyk"]},
        "status": {"privacyStatus": "private", "selfDeclaredMadeForKids": False, "license": "youtube",
                   "embeddable": True},
    }
    if m.get("pl"):
        zasob["localizations"] = {"pl": {"title": m["pl"]["title"], "description": m["pl"]["description"]}}
    vid = wgraj_plik(a.work / "final.mp4", zasob, "snippet,status" + (",localizations" if m.get("pl") else ""))
    print(f"  film: {vid}")
    miniatura = a.pakiet / m.get("thumbnail", "thumbnail-a.jpg")
    if miniatura.is_file():
        wyslij("POST", f"{UPLOAD}/thumbnails/set", parametry={"videoId": vid}, cialo=miniatura.read_bytes(),
               typ="image/jpeg")
        print("  miniatura")
    for jezyk, nazwa in (("en", "English"), ("pl", "Polski")):
        srt = a.work / f"napisy-{jezyk}.srt"
        if srt.is_file():
            cialo, typ = multipart({"snippet": {"videoId": vid, "language": jezyk, "name": nazwa, "isDraft": False}},
                                   srt, "application/x-subrip")
            wyslij("POST", f"{UPLOAD}/captions", parametry={"uploadType": "multipart", "part": "snippet"},
                   cialo=cialo, typ=typ)
            print(f"  napisy {jezyk}")
    if a.filar:
        pid = playlista(KONFIG["playlisty"].get(a.filar, a.filar))
        wyslij("POST", f"{API}/playlistItems", parametry={"part": "snippet"}, cialo={
            "snippet": {"playlistId": pid, "resourceId": {"kind": "youtube#video", "videoId": vid}}})
        print(f"  playlista {a.filar}")
    print(f"YT_ID={vid}")


def zaplanuj(video_id: str, termin: str) -> None:
    utc = datetime.fromisoformat(termin).astimezone(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    wyslij("PUT", f"{API}/videos", parametry={"part": "status"}, cialo={
        "id": video_id, "status": {"privacyStatus": "private", "publishAt": utc, "selfDeclaredMadeForKids": False}})
    print(f"OK: {video_id} zaplanowany na {utc}")


def short(a: argparse.Namespace) -> None:
    opisy = json.loads((a.pakiet / "shorts.json").read_text(encoding="utf-8"))
    nr = int(a.plik.stem.split("-")[-1]) - 1 if a.plik.stem.split("-")[-1].isdigit() else 0
    opis = opisy[min(nr, len(opisy) - 1)]
    utc = datetime.fromisoformat(a.termin).astimezone(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    vid = wgraj_plik(a.plik, {
        "snippet": {"title": opis["tytul"][:LIMIT_TYTULU],
                    "description": f"{opis.get('opis', '')}\n\nFull video: https://youtu.be/{a.film}\n\n"
                                   "Historical results, not investment advice. Past performance does not guarantee future results.",
                    "categoryId": KONFIG["kategoria_youtube"], "defaultLanguage": KONFIG["jezyk"]},
        "status": {"privacyStatus": "private", "publishAt": utc, "selfDeclaredMadeForKids": False}}, "snippet,status")
    print(f"YT_ID={vid}")


def main() -> None:
    global NA_SUCHO
    ap = argparse.ArgumentParser(description="D3 — YouTube Data API")
    ap.add_argument("--na-sucho", action="store_true")
    pod = ap.add_subparsers(dest="cmd", required=True)
    pod.add_parser("sprawdz", help="czy jest klient OAuth i token (bez sieci)")
    p = pod.add_parser("film")
    p.add_argument("--work", required=True, type=Path)
    p.add_argument("--pakiet", required=True, type=Path)
    p.add_argument("--filar", default="")
    p = pod.add_parser("zaplanuj")
    p.add_argument("video_id")
    p.add_argument("termin")
    p = pod.add_parser("short")
    p.add_argument("--plik", required=True, type=Path)
    p.add_argument("--pakiet", required=True, type=Path)
    p.add_argument("--film", required=True)
    p.add_argument("--termin", required=True)
    pod.add_parser("playlisty", help="F5: playlisty wszystkich filarów")
    a = ap.parse_args()
    NA_SUCHO = a.na_sucho
    try:
        if a.cmd == "sprawdz":
            if not yt_api.skonfigurowany():
                sys.exit(f"brak autoryzacji: {yt_api.KLIENT} i {yt_api.TOKEN}")
            print("OK: klient OAuth i token są")
        elif a.cmd == "film":
            film(a)
        elif a.cmd == "zaplanuj":
            zaplanuj(a.video_id, a.termin)
        elif a.cmd == "short":
            short(a)
        elif a.cmd == "playlisty":
            for filar, nazwa in KONFIG["playlisty"].items():
                print(f"{filar}: {playlista(nazwa)}")
    except BladApi as e:
        sys.exit(f"błąd: {e}")


if __name__ == "__main__":
    main()
