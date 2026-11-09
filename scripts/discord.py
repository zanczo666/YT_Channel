#!/usr/bin/env python3
"""G2 — powiadomienia i akceptacje przez Discord, bez stałego połączenia z bramką (gateway).

Bot wysyła wiadomość na kanał i dokłada dwie reakcje: ✅ (akceptuj) i 🔁 (popraw). Runner przy każdym
przebiegu sprawdza, którą kliknął właściciel, a uwagi zbiera z jego odpowiedzi na tę wiadomość. To daje
to samo co przyciski, a nie wymaga procesu, który nasłuchuje przez całą dobę.

Konfiguracja: `~/.config/yt_channel/discord.json` (chmod 600):
    {"token": "<token bota>", "kanal_id": "<ID kanału #produkcja>", "wlasciciel_id": "<Twoje ID użytkownika>"}
Bez pliku moduł nie wysyła nic: zapisuje powiadomienia do `content/pipeline/_powiadomienia.log`,
a akceptacje przyjmuje `runner.py akceptuj|popraw`.

    python3 scripts/discord.py test      wysyła wiadomość próbną
"""

from __future__ import annotations

import json
import sys
import urllib.error
import urllib.parse
import urllib.request
import uuid
from datetime import datetime
from pathlib import Path

KONFIG = Path.home() / ".config" / "yt_channel" / "discord.json"
API = "https://discord.com/api/v10"
LOG = Path(__file__).resolve().parent.parent / "content" / "pipeline" / "_powiadomienia.log"
AKCEPTUJ, POPRAW = "✅", "🔁"
MAX_ZNAKOW = 1900


def konfiguracja() -> dict | None:
    if not KONFIG.is_file():
        return None
    dane = json.loads(KONFIG.read_text(encoding="utf-8"))
    return dane if all(dane.get(k) for k in ("token", "kanal_id", "wlasciciel_id")) else None


def _zapytanie(metoda: str, sciezka: str, k: dict, dane: bytes | None = None,
               typ: str = "application/json") -> dict | list | None:
    req = urllib.request.Request(f"{API}{sciezka}", data=dane, method=metoda, headers={
        "Authorization": f"Bot {k['token']}", "Content-Type": typ,
        "User-Agent": "DiscordBot (https://github.com/zanczo666, 1.0)"})
    try:
        with urllib.request.urlopen(req, timeout=30) as r:
            tresc = r.read()
            return json.loads(tresc) if tresc else None
    except urllib.error.HTTPError as e:
        # token nie trafia do komunikatu: pokazujemy tylko kod i odpowiedź serwera
        raise RuntimeError(f"Discord {metoda} {sciezka.split('?')[0]}: HTTP {e.code} {e.read()[:200]!r}") from None


def _do_logu(tekst: str) -> None:
    LOG.parent.mkdir(parents=True, exist_ok=True)
    with LOG.open("a", encoding="utf-8") as f:
        f.write(f"{datetime.now():%Y-%m-%d %H:%M} {tekst}\n")


def wyslij(tekst: str, pliki: list[Path] | None = None) -> str | None:
    """Wiadomość z opcjonalnymi załącznikami. Zwraca ID wiadomości albo None bez konfiguracji."""
    k = konfiguracja()
    if not k:
        _do_logu(tekst.replace("\n", " | "))
        return None
    tresc = {"content": tekst[:MAX_ZNAKOW]}
    pliki = [p for p in (pliki or []) if p.is_file()][:4]
    if not pliki:
        odp = _zapytanie("POST", f"/channels/{k['kanal_id']}/messages", k, json.dumps(tresc).encode())
        return odp["id"]
    granica = uuid.uuid4().hex
    czesci = [f'--{granica}\r\nContent-Disposition: form-data; name="payload_json"\r\n'
              f'Content-Type: application/json\r\n\r\n{json.dumps(tresc)}\r\n'.encode()]
    for i, p in enumerate(pliki):
        czesci.append(f'--{granica}\r\nContent-Disposition: form-data; name="files[{i}]"; '
                      f'filename="{p.name}"\r\nContent-Type: application/octet-stream\r\n\r\n'.encode()
                      + p.read_bytes() + b"\r\n")
    czesci.append(f"--{granica}--\r\n".encode())
    odp = _zapytanie("POST", f"/channels/{k['kanal_id']}/messages", k, b"".join(czesci),
                     f"multipart/form-data; boundary={granica}")
    return odp["id"]


def popros_o_akceptacje(tekst: str, pliki: list[Path] | None = None) -> str | None:
    mid = wyslij(f"{tekst}\n\n{AKCEPTUJ} akceptuj   {POPRAW} popraw (uwagi napisz w odpowiedzi na tę wiadomość)", pliki)
    k = konfiguracja()
    if mid and k:
        for emoji in (AKCEPTUJ, POPRAW):
            _zapytanie("PUT", f"/channels/{k['kanal_id']}/messages/{mid}/reactions/"
                              f"{urllib.parse.quote(emoji)}/@me", k)
    return mid


def decyzja(mid: str) -> tuple[str | None, str]:
    """('akceptuj' | 'popraw' | None, uwagi). Liczy się wyłącznie reakcja i odpowiedź właściciela."""
    k = konfiguracja()
    if not k or not mid:
        return None, ""
    def klikniete(emoji: str) -> bool:
        uzytkownicy = _zapytanie("GET", f"/channels/{k['kanal_id']}/messages/{mid}/reactions/"
                                        f"{urllib.parse.quote(emoji)}", k) or []
        return any(u["id"] == str(k["wlasciciel_id"]) for u in uzytkownicy)
    odpowiedzi = _zapytanie("GET", f"/channels/{k['kanal_id']}/messages?after={mid}&limit=100", k) or []
    uwagi = "\n".join(m["content"] for m in reversed(odpowiedzi)
                      if m["author"]["id"] == str(k["wlasciciel_id"])
                      and (m.get("message_reference") or {}).get("message_id") == mid)
    if klikniete(POPRAW):
        return "popraw", uwagi
    if klikniete(AKCEPTUJ):
        return "akceptuj", uwagi
    return None, uwagi


if __name__ == "__main__":
    if sys.argv[1:] == ["test"]:
        mid = wyslij("YT_Channel: wiadomość próbna z runnera.")
        print("wysłano" if mid else f"brak konfiguracji ({KONFIG}); zapisano do {LOG}")
    else:
        sys.exit(__doc__)
