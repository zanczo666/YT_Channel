#!/usr/bin/env python3
"""G5 — dostęp do YouTube Data/Analytics API przez OAuth: autoryzacja raz, potem odświeżany token.

Pliki (chmod 600, nigdy w repo ani w logach):
- `~/.config/yt_channel/youtube_oauth_client.json` — klient OAuth typu „Desktop app” z Google Cloud Console
  (projekt yt-channel-research-513011, włączone YouTube Data API v3 i YouTube Analytics API),
- `~/.config/yt_channel/youtube_token.json` — token odświeżania, tworzy go `autoryzuj`.

Autoryzacja na serwerze bez przeglądarki: otwórz tunel `ssh -L 8765:localhost:8765 claudecore`,
uruchom `python3 scripts/yt_api.py autoryzuj` i otwórz wypisany link na komputerze. Bez tunelu przeglądarka
pokaże błąd połączenia — wtedy skopiuj adres z paska i wklej go tutaj.

    python3 scripts/yt_api.py autoryzuj | sprawdz
"""

from __future__ import annotations

import http.server
import json
import os
import secrets
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

KATALOG = Path.home() / ".config" / "yt_channel"
KLIENT = KATALOG / "youtube_oauth_client.json"
TOKEN = KATALOG / "youtube_token.json"
ZAKRESY = ["https://www.googleapis.com/auth/youtube",
           "https://www.googleapis.com/auth/youtube.force-ssl",     # napisy i odpowiedzi na komentarze
           "https://www.googleapis.com/auth/yt-analytics.readonly"]
PORT = 8765
API = "https://www.googleapis.com/youtube/v3"
UPLOAD = "https://www.googleapis.com/upload/youtube/v3"
ANALYTICS = "https://youtubeanalytics.googleapis.com/v2/reports"
_dostep: dict = {}


class BladApi(RuntimeError):
    pass


def klient() -> dict:
    if not KLIENT.is_file():
        raise BladApi(f"brak {KLIENT} — pobierz klienta OAuth (Desktop app) z Google Cloud Console")
    dane = json.loads(KLIENT.read_text(encoding="utf-8"))
    return dane.get("installed") or dane.get("web") or dane


def skonfigurowany() -> bool:
    return KLIENT.is_file() and TOKEN.is_file()


def _post_formularz(url: str, pola: dict) -> dict:
    req = urllib.request.Request(url, data=urllib.parse.urlencode(pola).encode(), method="POST")
    try:
        with urllib.request.urlopen(req, timeout=30) as r:
            return json.loads(r.read())
    except urllib.error.HTTPError as e:
        raise BladApi(f"OAuth HTTP {e.code}: {e.read()[:300]!r}") from None


def autoryzuj() -> None:
    k = klient()
    stan = secrets.token_urlsafe(16)
    przekierowanie = f"http://localhost:{PORT}/"
    url = "https://accounts.google.com/o/oauth2/v2/auth?" + urllib.parse.urlencode({
        "client_id": k["client_id"], "redirect_uri": przekierowanie, "response_type": "code",
        "scope": " ".join(ZAKRESY), "access_type": "offline", "prompt": "consent", "state": stan})
    print(f"Otwórz na komputerze (z tunelem ssh -L {PORT}:localhost:{PORT} claudecore):\n\n{url}\n")
    kod: dict = {}

    class Odbior(http.server.BaseHTTPRequestHandler):
        def do_GET(self):  # noqa: N802
            kod.update(dict(urllib.parse.parse_qsl(urllib.parse.urlparse(self.path).query)))
            self.send_response(200)
            self.end_headers()
            self.wfile.write("Autoryzacja odebrana, możesz zamknąć kartę.".encode())

        def log_message(self, *a):
            pass

    try:
        serwer = http.server.HTTPServer(("127.0.0.1", PORT), Odbior)
        serwer.timeout = 300
        print("Czekam na przekierowanie (5 min)… albo przerwij Ctrl+C i wklej adres ręcznie.")
        serwer.handle_request()
    except KeyboardInterrupt:
        pass
    if "code" not in kod:
        adres = input("Wklej adres z paska przeglądarki: ").strip()
        kod.update(dict(urllib.parse.parse_qsl(urllib.parse.urlparse(adres).query)))
    if kod.get("state") != stan or "code" not in kod:
        sys.exit("błąd: brak kodu albo niezgodny parametr state")
    tok = _post_formularz("https://oauth2.googleapis.com/token", {
        "code": kod["code"], "client_id": k["client_id"], "client_secret": k["client_secret"],
        "redirect_uri": przekierowanie, "grant_type": "authorization_code"})
    if "refresh_token" not in tok:
        sys.exit("błąd: Google nie zwrócił tokenu odświeżania")
    KATALOG.mkdir(parents=True, exist_ok=True)
    TOKEN.touch(mode=0o600, exist_ok=True)
    os.chmod(TOKEN, 0o600)
    TOKEN.write_text(json.dumps({"refresh_token": tok["refresh_token"], "scope": tok.get("scope")}), encoding="utf-8")
    print(f"OK: token zapisany w {TOKEN}")


def token_dostepu() -> str:
    if _dostep.get("wygasa", 0) > time.time() + 60:
        return _dostep["token"]
    if not TOKEN.is_file():
        raise BladApi(f"brak {TOKEN} — uruchom: python3 scripts/yt_api.py autoryzuj")
    k = klient()
    tok = _post_formularz("https://oauth2.googleapis.com/token", {
        "client_id": k["client_id"], "client_secret": k["client_secret"],
        "refresh_token": json.loads(TOKEN.read_text())["refresh_token"], "grant_type": "refresh_token"})
    _dostep.update(token=tok["access_token"], wygasa=time.time() + tok.get("expires_in", 3600))
    return _dostep["token"]


def zapytanie(metoda: str, url: str, parametry: dict | None = None, cialo: dict | bytes | None = None,
              typ: str = "application/json", naglowki: dict | None = None,
              surowa: bool = False):
    if parametry:
        url += ("&" if "?" in url else "?") + urllib.parse.urlencode(parametry)
    dane = json.dumps(cialo).encode() if isinstance(cialo, dict) else cialo
    req = urllib.request.Request(url, data=dane, method=metoda, headers={
        "Authorization": f"Bearer {token_dostepu()}", **({"Content-Type": typ} if dane is not None else {}),
        **(naglowki or {})})
    try:
        r = urllib.request.urlopen(req, timeout=300)
    except urllib.error.HTTPError as e:
        if surowa and e.code == 308:      # wznawialne wysyłanie: „ciąg dalszy”, nie błąd
            return e
        raise BladApi(f"YouTube {metoda} {url.split('?')[0]}: HTTP {e.code} {e.read()[:400]!r}") from None
    if surowa:
        return r
    tresc = r.read()
    return json.loads(tresc) if tresc else {}


if __name__ == "__main__":
    if sys.argv[1:] == ["autoryzuj"]:
        autoryzuj()
    elif sys.argv[1:] == ["sprawdz"]:
        try:
            token_dostepu()
            kanal = zapytanie("GET", f"{API}/channels", {"part": "snippet", "mine": "true"})
            print("OK:", ", ".join(i["snippet"]["title"] for i in kanal.get("items", [])) or "brak kanału")
        except BladApi as e:
            sys.exit(f"błąd: {e}")
    else:
        sys.exit(__doc__)
