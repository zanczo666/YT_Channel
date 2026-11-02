#!/usr/bin/env python3
"""G3 — worker on-demand w Hetznerze: postaw, wykonaj ciężkie kroki, zabierz wynik, skasuj.

Ciężka część montażu (transkrypcja, render) nie należy do `claudecore`: tam działa kilkanaście sesji
Claude Code przy 7 GB RAM bez swapu, a render potrafi je ubić (OOM 2026-11-02). Worker jest jednorazowy:
wstaje na czas zadania i znika.

Polecenia:
    worker.py up                      postaw maszynę (łańcuch fallbacku G3a) i poczekaj na SSH
    worker.py job --work <kat> --script <plik> --video <plik>
                                      pełny cykl: postaw → wyślij → C1–C5 → zabierz wynik → skasuj
    worker.py down                    skasuj maszynę
    worker.py reap [--older-than 1]   watchdog G7: kasuje workery starsze niż N godzin

Rozliczenie Hetznera idzie za **pełną rozpoczętą godzinę**, więc nie ma sensu skracać pracy poniżej
godziny — za to oba filmy z jednej sesji nagraniowej opłaca się zmontować w jednym uruchomieniu.
Przy błędzie maszyna **nie jest kasowana od razu** (`--keep-on-error`): godzina i tak jest opłacona,
a bez logów z żywej maszyny diagnoza jest niemożliwa; dobije ją `reap`.

Token: `~/.config/yt_channel/hetzner_api_token` (chmod 600). Klucz SSH: `~/.ssh/yt_worker`.
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
import time
import urllib.error
import urllib.request
from datetime import datetime, timedelta, timezone
from pathlib import Path

API = "https://api.hetzner.cloud/v1"
TOKEN_PATH = Path.home() / ".config/yt_channel/hetzner_api_token"
KLUCZ = Path.home() / ".ssh/yt_worker"
NAZWA = "yt-worker"
ETYKIETY = {"role": "yt-worker", "projekt": "yt-channel"}
OBRAZ = "ubuntu-24.04"          # ta sama wersja co claudecore — debugujemy lokalnie, uruchamiamy zdalnie

# G3a: typ ważniejszy niż lokalizacja. claudecore stoi w Helsinkach, więc hel1 jest pierwszy
# (ten sam DC co źródło danych); dalej zgodnie z preferencją właściciela fsn1, potem nbg1.
LANCUCH = [("ccx33", "hel1"), ("ccx33", "fsn1"), ("ccx33", "nbg1"),
           ("cpx42", "hel1"), ("cx43", "hel1")]

CLOUD_INIT = """#cloud-config
package_update: true
packages: [ffmpeg, python3-venv, python3-pip, rsync]
runcmd:
  - [bash, -lc, "python3 -m venv /opt/whisper && /opt/whisper/bin/pip install -q faster-whisper numpy"]
  - [bash, -lc, "touch /var/lib/yt-worker-gotowy"]
"""


def token() -> str:
    if not TOKEN_PATH.is_file():
        sys.exit(f"błąd: brak tokenu {TOKEN_PATH}\n"
                 f"Utwórz token (Hetzner Console → Security → API tokens, uprawnienie Read & Write) i zapisz:\n"
                 f"  install -m 600 /dev/null {TOKEN_PATH} && nano {TOKEN_PATH}")
    t = TOKEN_PATH.read_text(encoding="utf-8").strip()
    if not t:
        sys.exit(f"błąd: {TOKEN_PATH} jest pusty")
    return t


def api(sciezka: str, metoda: str = "GET", dane: dict | None = None) -> dict:
    """Wywołanie API Hetznera. Token nigdy nie trafia do logów ani do komunikatów błędów."""
    req = urllib.request.Request(
        f"{API}{sciezka}", method=metoda,
        data=json.dumps(dane).encode() if dane else None,
        headers={"Authorization": f"Bearer {token()}", "Content-Type": "application/json"})
    try:
        with urllib.request.urlopen(req, timeout=60) as r:
            tresc = r.read().decode()
            return json.loads(tresc) if tresc else {}
    except urllib.error.HTTPError as e:
        tresc = e.read().decode()
        try:
            blad = json.loads(tresc)["error"]
            raise RuntimeError(f"{blad.get('code')}: {blad.get('message')}") from None
        except (KeyError, json.JSONDecodeError):
            raise RuntimeError(f"HTTP {e.code}: {tresc[:300]}") from None


def zapewnij_klucz() -> int:
    """Klucz SSH workera w koncie Hetznera (dodawany raz, rozpoznawany po nazwie)."""
    pub = Path(f"{KLUCZ}.pub")
    if not pub.is_file():
        sys.exit(f"błąd: brak klucza {pub} — utwórz go:\n  ssh-keygen -t ed25519 -f {KLUCZ} -N ''")
    istniejace = api("/ssh_keys")["ssh_keys"]
    for k in istniejace:
        if k["name"] == NAZWA:
            return k["id"]
    return api("/ssh_keys", "POST", {"name": NAZWA, "public_key": pub.read_text().strip()})["ssh_key"]["id"]


def znajdz() -> dict | None:
    serwery = api(f"/servers?label_selector=role={ETYKIETY['role']}")["servers"]
    return serwery[0] if serwery else None


def adres(serwer: dict) -> str:
    ipv4 = (serwer.get("public_net") or {}).get("ipv4")
    if ipv4 and ipv4.get("ip"):
        return ipv4["ip"]
    ipv6 = (serwer.get("public_net") or {}).get("ipv6")
    if ipv6 and ipv6.get("ip"):
        return ipv6["ip"].replace("/64", "1")
    sys.exit("błąd: serwer nie ma adresu publicznego")


def ssh(host: str, polecenie: str, cicho: bool = False) -> subprocess.CompletedProcess:
    return subprocess.run(
        ["ssh", "-i", str(KLUCZ), "-o", "StrictHostKeyChecking=no", "-o", "UserKnownHostsFile=/dev/null",
         "-o", "LogLevel=ERROR", "-o", "ConnectTimeout=10", f"root@{host}", polecenie],
        capture_output=cicho, text=True)


def czekaj_na_gotowosc(host: str, minuty: int = 12) -> None:
    """Czeka na SSH, a potem na znacznik z cloud-init (FFmpeg i venv zainstalowane)."""
    koniec = time.time() + minuty * 60
    print("czekam na SSH…", end="", flush=True)
    while time.time() < koniec:
        if ssh(host, "true", cicho=True).returncode == 0:
            print(" jest")
            break
        print(".", end="", flush=True)
        time.sleep(5)
    else:
        sys.exit("\nbłąd: maszyna nie wpuściła po SSH w zadanym czasie")

    print("czekam na instalację (cloud-init)…", end="", flush=True)
    while time.time() < koniec:
        if ssh(host, "test -f /var/lib/yt-worker-gotowy", cicho=True).returncode == 0:
            print(" gotowe")
            return
        print(".", end="", flush=True)
        time.sleep(10)
    sys.exit("\nbłąd: cloud-init nie skończył instalacji — zajrzyj na maszynę: "
             f"ssh -i {KLUCZ} root@{host} 'cloud-init status --long'")


def postaw() -> dict:
    """Łańcuch fallbacku G3a: pierwszy typ i lokalizacja, które są dostępne."""
    if znajdz():
        sys.exit("błąd: worker już istnieje — użyj `worker.py down` albo poczekaj na koniec zadania")
    klucz_id = zapewnij_klucz()
    bledy = []
    for typ, lokalizacja in LANCUCH:
        try:
            print(f"próbuję {typ} @ {lokalizacja}…")
            odp = api("/servers", "POST", {
                "name": f"{NAZWA}-{int(time.time())}", "server_type": typ, "location": lokalizacja,
                "image": OBRAZ, "ssh_keys": [klucz_id], "labels": ETYKIETY,
                "user_data": CLOUD_INIT, "start_after_create": True,
                "public_net": {"enable_ipv4": True, "enable_ipv6": True},
            })
            serwer = odp["server"]
            print(f"postawiony: {serwer['name']} ({typ} @ {lokalizacja}), {adres(serwer)}")
            return serwer
        except RuntimeError as e:
            bledy.append(f"  {typ} @ {lokalizacja}: {e}")
    sys.exit("błąd: żaden wariant z łańcucha nie wstał:\n" + "\n".join(bledy))


def skasuj(serwer: dict | None = None) -> None:
    serwer = serwer or znajdz()
    if not serwer:
        print("nie ma czego kasować")
        return
    api(f"/servers/{serwer['id']}", "DELETE")
    print(f"skasowany: {serwer['name']}")


def reap(godziny: float) -> None:
    """G7 — watchdog kosztów: maszyna, która przeżyła zadanie, płaci dalej."""
    prog = datetime.now(timezone.utc) - timedelta(hours=godziny)
    ilu = 0
    for s in api(f"/servers?label_selector=role={ETYKIETY['role']}")["servers"]:
        powstal = datetime.fromisoformat(s["created"].replace("Z", "+00:00"))
        if powstal < prog:
            api(f"/servers/{s['id']}", "DELETE")
            print(f"skasowany (wiek {datetime.now(timezone.utc) - powstal}): {s['name']}")
            ilu += 1
    print(f"watchdog: skasowano {ilu}")


def job(a: argparse.Namespace) -> None:
    """Pełny cykl: postaw → wyślij → C1–C5 → zabierz wynik → skasuj."""
    repo = Path(__file__).resolve().parent
    serwer = postaw()
    host = adres(serwer)
    udalo_sie = False
    try:
        czekaj_na_gotowosc(host)
        ssh(host, "mkdir -p /root/praca /root/scripts")
        subprocess.run(["rsync", "-az", "-e", f"ssh -i {KLUCZ} -o StrictHostKeyChecking=no "
                                              f"-o UserKnownHostsFile=/dev/null -o LogLevel=ERROR",
                        f"{repo}/", f"root@{host}:/root/scripts/"], check=True)
        for plik in (a.video, a.script):
            subprocess.run(["rsync", "-az", "--progress", "-e", f"ssh -i {KLUCZ} "
                            f"-o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null -o LogLevel=ERROR",
                            str(plik), f"root@{host}:/root/praca/"], check=True)

        video = f"/root/praca/{Path(a.video).name}"
        scen = f"/root/praca/{Path(a.script).name}"
        kroki = [
            ("C1 ingest",    f"python3 /root/scripts/ingest.py --in {video} --work /root/praca/work --normalize"),
            ("C2 transkrypcja", f"/opt/whisper/bin/python /root/scripts/transcribe.py "
                                f"--work /root/praca/work --model {a.model} --threads 8"),
            ("C3 dopasowanie", f"python3 /root/scripts/align.py --work /root/praca/work --script {scen}"),
            ("C4 montaż",     f"python3 /root/scripts/cut.py --work /root/praca/work --video {video} --mem-max 0"),
            ("C5 dźwięk",     f"python3 /root/scripts/audio_master.py --work /root/praca/work --mem-max 0"),
        ]
        for nazwa, polecenie in kroki:
            print(f"\n── {nazwa} ──")
            if ssh(host, f"cd /root/praca && {polecenie} 2>&1 | tee -a /root/praca/work/log.txt").returncode != 0:
                raise RuntimeError(f"{nazwa} nie powiodło się")

        # G8: wynik i logi ściągamy zanim maszyna zniknie
        a.work.mkdir(parents=True, exist_ok=True)
        subprocess.run(["rsync", "-az", "-e", f"ssh -i {KLUCZ} -o StrictHostKeyChecking=no "
                        f"-o UserKnownHostsFile=/dev/null -o LogLevel=ERROR",
                        f"root@{host}:/root/praca/work/", f"{a.work}/"], check=True)
        udalo_sie = True
        print(f"\nOK: wynik w {a.work}")
    finally:
        if udalo_sie or not a.keep_on_error:
            skasuj(serwer)
        else:
            print(f"\nmaszyna ZOSTAJE do diagnozy (godzina i tak opłacona): "
                  f"ssh -i {KLUCZ} root@{host}\nskasuj: python3 scripts/worker.py down")


def main() -> None:
    ap = argparse.ArgumentParser(description="G3 — worker on-demand")
    pod = ap.add_subparsers(dest="cmd", required=True)
    pod.add_parser("up", help="postaw maszynę")
    pod.add_parser("down", help="skasuj maszynę")
    p_reap = pod.add_parser("reap", help="watchdog kosztów")
    p_reap.add_argument("--older-than", type=float, default=1.0, help="wiek w godzinach")
    p_job = pod.add_parser("job", help="pełny cykl C1–C5")
    p_job.add_argument("--work", required=True, type=Path, help="katalog na wynik (lokalnie)")
    p_job.add_argument("--video", required=True, type=Path)
    p_job.add_argument("--script", required=True, type=Path)
    p_job.add_argument("--model", default="large-v3")
    p_job.add_argument("--keep-on-error", action="store_true", default=True)
    a = ap.parse_args()

    if a.cmd == "up":
        serwer = postaw()
        czekaj_na_gotowosc(adres(serwer))
        print(f"gotowe: ssh -i {KLUCZ} root@{adres(serwer)}")
    elif a.cmd == "down":
        skasuj()
    elif a.cmd == "reap":
        reap(a.older_than)
    else:
        job(a)


if __name__ == "__main__":
    main()
