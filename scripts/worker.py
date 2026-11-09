#!/usr/bin/env python3
"""G3 — worker on-demand w Hetznerze: postaw, wykonaj ciężkie kroki, zabierz wynik, skasuj.

Ciężka część montażu (transkrypcja, render) nie należy do `claudecore`: tam działa kilkanaście sesji
Claude Code przy 7 GB RAM bez swapu, a render potrafi je ubić (OOM 2026-11-02). Worker jest jednorazowy:
wstaje na czas zadania i znika.

Polecenia:
    worker.py up                      postaw maszynę (łańcuch fallbacku G3a) i poczekaj na SSH
    worker.py job --work <kat> --script <plik> --video <plik>
                                      pełny cykl: postaw → wyślij → C1–C12 → zabierz wynik → skasuj
    worker.py job --work <kat> --film <wideo> <scenariusz> [dane] --film …
                                      kilka filmów z jednej sesji nagraniowej w jednym uruchomieniu (B4)
    worker.py snapshot build|list|promote <id>|prune
                                      G3b: obraz z gotowym środowiskiem, budowany skryptem z repo
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
import os
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

# G3c: wszystko, czego potrzebują kroki montażu i miniatur. Wersje pip są przypięte w `config/requirements-*.txt`,
# osobno dla każdego venv (pierwsza budowa bez plików zapisuje `pip freeze`, który od tej pory jest wzorcem).
PAKIETY = ["ffmpeg", "python3-venv", "python3-pip", "python3-pil", "fonts-urw-base35", "rsync", "tesseract-ocr"]
KONFIG = Path(__file__).resolve().parent.parent / "config"
WYMAGANIA = {"whisper": KONFIG / "requirements-whisper.txt", "narzedzia": KONFIG / "requirements-narzedzia.txt"}
BEZ_PRZYPIEC = {"whisper": "faster-whisper numpy",
                "narzedzia": "pillow numpy opencv-contrib-python-headless pytesseract playwright rembg onnxruntime"}
MODEL_WHISPER = "large-v3"
ZNACZNIK = "/var/lib/yt-worker-gotowy"

CLOUD_INIT = f"""#cloud-config
package_update: true
packages: [{", ".join(PAKIETY)}]
runcmd:
  - [bash, -lc, "python3 -m venv /opt/whisper && /opt/whisper/bin/pip install -q faster-whisper numpy"]
  - [bash, -lc, "touch {ZNACZNIK}"]
"""
# maszyna ze snapshotu ma już wszystko i znacznik gotowości; cloud-init nie robi nic
CLOUD_INIT_SNAPSHOT = "#cloud-config\n"

# Snapshot budujemy na najmniejszej maszynie: obraz da się postawić tylko na dysku co najmniej tak dużym
# jak źródłowy, a cały łańcuch fallbacku musi z niego korzystać.
BUDOWA = [("cx23", "hel1"), ("cpx22", "hel1"), ("cx33", "hel1"), ("cx23", "fsn1"), ("cpx22", "fsn1")]
ETYKIETA_OBRAZU = "yt-worker-obraz"
ZOSTAW_OBRAZOW = 2


PLIK_JOBA = Path.home() / ".local" / "state" / "yt_channel" / "worker-job.pid"
TWARDY_LIMIT_H = 3.0


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


def obrazy() -> list[dict]:
    """Nasze snapshoty, od najnowszego."""
    lista = api(f"/images?type=snapshot&label_selector=role={ETYKIETA_OBRAZU}")["images"]
    return sorted(lista, key=lambda i: i["created"], reverse=True)


def obraz_do_startu(wybor: str) -> tuple[str | int, str]:
    """`produkcja` (domyślnie), `kandydat` (test nowego obrazu), `czysty` (Ubuntu + cloud-init) albo ID."""
    if wybor == "czysty":
        return OBRAZ, CLOUD_INIT
    if wybor.isdigit():
        return int(wybor), CLOUD_INIT_SNAPSHOT
    pasujace = [i for i in obrazy() if i["labels"].get("status") == wybor]
    if pasujace:
        print(f"obraz: snapshot {pasujace[0]['id']} ({wybor}, {pasujace[0]['description']})")
        return pasujace[0]["id"], CLOUD_INIT_SNAPSHOT
    if wybor == "kandydat":
        sys.exit("błąd: nie ma snapshotu-kandydata; zbuduj go: worker.py snapshot build")
    print("obraz: brak snapshotu produkcyjnego, stawiam czyste Ubuntu z instalacją (~6 min dłużej)")
    return OBRAZ, CLOUD_INIT


def postaw(obraz: str = "produkcja", lancuch: list[tuple[str, str]] | None = None,
           etykiety: dict | None = None) -> dict:
    """Łańcuch fallbacku G3a: pierwszy typ i lokalizacja, które są dostępne."""
    if znajdz():
        sys.exit("błąd: worker już istnieje — użyj `worker.py down` albo poczekaj na koniec zadania")
    klucz_id = zapewnij_klucz()
    obraz_id, user_data = obraz_do_startu(obraz)
    bledy = []
    for typ, lokalizacja in lancuch or LANCUCH:
        try:
            print(f"próbuję {typ} @ {lokalizacja}…")
            odp = api("/servers", "POST", {
                "name": f"{NAZWA}-{int(time.time())}", "server_type": typ, "location": lokalizacja,
                "image": obraz_id, "ssh_keys": [klucz_id], "labels": etykiety or ETYKIETY,
                "user_data": user_data, "start_after_create": True,
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


def czekaj_na_akcje(akcja: dict, minuty: int = 40) -> None:
    koniec = time.time() + minuty * 60
    while time.time() < koniec:
        stan = api(f"/actions/{akcja['id']}")["action"]
        if stan["status"] == "success":
            return
        if stan["status"] == "error":
            raise RuntimeError(f"akcja {akcja['command']}: {stan.get('error')}")
        time.sleep(15)
    raise RuntimeError(f"akcja {akcja['command']} trwa ponad {minuty} min")


def rsync_do(host: str, zrodlo: str, cel: str, *opcje: str) -> None:
    subprocess.run(["rsync", "-az", *opcje, "-e", f"ssh -i {KLUCZ} -o StrictHostKeyChecking=no "
                    f"-o UserKnownHostsFile=/dev/null -o LogLevel=ERROR", zrodlo, cel], check=True)


def snapshot_build() -> None:
    """G3b: czysta maszyna → instalacja z przypiętych wersji → snapshot-kandydat → skasowanie maszyny."""
    PLIK_JOBA.parent.mkdir(parents=True, exist_ok=True)
    PLIK_JOBA.write_text(str(os.getpid()))      # watchdog nie może skasować maszyny w trakcie budowy
    serwer = postaw("czysty", BUDOWA)
    host = adres(serwer)
    try:
        czekaj_na_gotowosc(host, minuty=20)
        ssh(host, "python3 -m venv /opt/narzedzia")
        pip = []
        for venv, plik in WYMAGANIA.items():
            if plik.is_file():
                rsync_do(host, str(plik), f"root@{host}:/root/{plik.name}")
                pip.append(f"/opt/{venv}/bin/pip install -q -r /root/{plik.name}")
            else:
                pip.append(f"/opt/{venv}/bin/pip install -q {BEZ_PRZYPIEC[venv]}")
        instalacja = [
            # dwa venv: whisper ma własne zależności (ctranslate2), których nie mieszamy z narzędziami miniatur
            *pip,
            # samo pobranie wag: załadowanie large-v3 na maszynie budującej (4 GB RAM) kończyło się brakiem pamięci
            f"/opt/whisper/bin/python -c \"from faster_whisper.utils import download_model; "
            f"print(download_model('{MODEL_WHISPER}'))\"",
            "/opt/narzedzia/bin/playwright install --with-deps chromium",
            # model, którego używa face_cutout.py; domyślny rembg zmienia się między wersjami
            "/opt/narzedzia/bin/python -c 'import rembg; rembg.new_session(\"u2net_human_seg\")'",
            "/opt/whisper/bin/pip freeze > /root/wersje-whisper.txt && "
            "/opt/narzedzia/bin/pip freeze > /root/wersje-narzedzia.txt",
            "(ffmpeg -version | head -1; tesseract --version 2>&1 | head -1; lsb_release -ds) > /root/wersje-system.txt",
            "cloud-init clean --logs && rm -rf /root/.cache/pip /var/cache/apt/archives/*.deb",
        ]
        for polecenie in instalacja:
            print(f"\n── {polecenie[:90]} ──")
            # pobieranie z GitHuba i Hugging Face potrafi chwilowo zwrócić 504: trzy podejścia z przerwą
            if ssh(host, f"for i in 1 2 3; do ( {polecenie} ) && exit 0; sleep 30; done; exit 1").returncode != 0:
                raise RuntimeError(f"instalacja nie powiodła się: {polecenie[:90]}")
        KONFIG.mkdir(exist_ok=True)
        rsync_do(host, f"root@{host}:/root/wersje-system.txt", str(KONFIG / "wersje-systemu-workera.txt"))
        for venv, plik in WYMAGANIA.items():
            if not plik.is_file():
                rsync_do(host, f"root@{host}:/root/wersje-{venv}.txt", str(plik))
                print(f"zapisano przypięte wersje: {plik} (zacommituj)")
        ssh(host, "sync")
        akcja = api(f"/servers/{serwer['id']}/actions/create_image", "POST", {
            "type": "snapshot", "description": f"yt-worker {datetime.now():%Y-%m-%d %H:%M}",
            "labels": {"role": ETYKIETA_OBRAZU, "status": "kandydat"}})
        print("tworzę snapshot…")
        czekaj_na_akcje(akcja["action"])
        print(f"OK: snapshot {akcja['image']['id']} jako kandydat; przetestuj: "
              f"worker.py job --obraz kandydat …, potem worker.py snapshot promote {akcja['image']['id']}")
    finally:
        PLIK_JOBA.unlink(missing_ok=True)
        skasuj(serwer)


def snapshot_promote(obraz_id: int) -> None:
    """Kandydat po teście na filmie staje się produkcyjnym; poprzedni produkcyjny zostaje jako zapasowy."""
    for i in obrazy():
        if i["labels"].get("status") == "produkcja":
            api(f"/images/{i['id']}", "PUT", {"labels": {"role": ETYKIETA_OBRAZU, "status": "poprzedni"}})
    api(f"/images/{obraz_id}", "PUT", {"labels": {"role": ETYKIETA_OBRAZU, "status": "produkcja"}})
    print(f"OK: snapshot {obraz_id} jest produkcyjny")


def snapshot_prune() -> None:
    """Snapshot kosztuje co miesiąc: zostaje produkcyjny, kandydat i najwyżej jeden poprzedni."""
    poprzednie = [i for i in obrazy() if i["labels"].get("status") == "poprzedni"]
    for i in poprzednie[ZOSTAW_OBRAZOW - 1:]:
        api(f"/images/{i['id']}", "DELETE")
        print(f"usunięty snapshot {i['id']} ({i['description']})")


def job_dziala() -> bool:
    """Czy na tym serwerze trwa `job`. Plik po zabitym procesie nic nie znaczy, więc sprawdzamy sam proces."""
    try:
        os.kill(int(PLIK_JOBA.read_text().strip()), 0)
    except (OSError, ValueError):
        return False
    return True


def reap(godziny: float) -> None:
    """G7 — watchdog kosztów: maszyna, która przeżyła zadanie, płaci dalej.

    Rozliczamy pełne rozpoczęte godziny, więc kasujemy tuż przed kolejną. Trwającego zadania nie ruszamy:
    utrata montażu kosztuje więcej niż dodatkowa godzina. Górny limit chroni przed zawieszonym zadaniem.
    """
    teraz = datetime.now(timezone.utc)
    prog = teraz - timedelta(hours=godziny)
    twardy_prog = teraz - timedelta(hours=TWARDY_LIMIT_H)
    trwa_job = job_dziala()
    ilu = 0
    for s in api(f"/servers?label_selector=role={ETYKIETY['role']}")["servers"]:
        powstal = datetime.fromisoformat(s["created"].replace("Z", "+00:00"))
        if powstal < prog and (not trwa_job or powstal < twardy_prog):
            api(f"/servers/{s['id']}", "DELETE")
            print(f"skasowany (wiek {teraz - powstal}): {s['name']}")
            ilu += 1
    if ilu:          # timer działa co minutę, więc puste przebiegi tylko zaśmiecałyby dziennik
        print(f"watchdog: skasowano {ilu}")


def kroki_filmu(a: argparse.Namespace, katalog: str, video: str, scen: str, dane: str | None,
                belka: bool) -> list[tuple[str, str]]:
    w = f"{katalog}/work"
    return [
        ("C1 ingest",    f"python3 /root/scripts/ingest.py --in {video} --work {w} --normalize"),
        ("C2 transkrypcja", f"/opt/whisper/bin/python /root/scripts/transcribe.py "
                            f"--work {w} --model {a.model} --threads 8"),
        ("C3 dopasowanie", f"python3 /root/scripts/align.py --work {w} --script {scen}"),
        ("C4 montaż",     f"python3 /root/scripts/cut.py --work {w} --video {video} --mem-max 0"),
        ("C5 dźwięk",     f"python3 /root/scripts/audio_master.py --work {w} --mem-max 0"),
        # podgląd powstaje zawsze: bez niego nie ma czego zatwierdzić przed wyborem --kolor
        ("C6 podgląd",    f"python3 /root/scripts/grade.py --work {w} --podglad --mem-max 0"),
        *([("C6 kolor",   f"python3 /root/scripts/grade.py --work {w} --styl {a.kolor} --mem-max 0")]
          if a.kolor else []),
        *([("C7 grafiki", f"python3 /root/scripts/graphics.py --work {w} "
                          f"--in {'kolor.mp4' if a.kolor else 'master.mp4'} --script {scen} --mem-max 0"
                          + (f" --dane {dane}" if dane else ""))]
          if dane or belka else []),
        ("C8 napisy",     f"python3 /root/scripts/subtitles.py --work {w} --script {scen}"),
        ("C9 rozdziały",  f"python3 /root/scripts/chapters.py --work {w} --script {scen}"),
        ("C11 render",    f"python3 /root/scripts/finish.py --work {w} --mem-max 0"
                          + (" --intro" if a.intro else "")),
        ("C12 kontrola",  f"python3 /root/scripts/qc.py --work {w} --mem-max 0"),
    ]


LEKKIE = ["--include=*/", "--include=*.json", "--include=*.md", "--include=*.txt", "--include=*.srt",
          "--include=*.jpg", "--include=*.edl", "--exclude=*"]


def job(a: argparse.Namespace) -> None:
    """Pełny cykl: postaw → wyślij → C1–C12 dla każdego filmu → zabierz wynik → skasuj."""
    filmy = [tuple(f) for f in (a.film or [])]
    if a.video or a.script:
        if not (a.video and a.script):
            sys.exit("błąd: --video i --script podaje się razem")
        filmy.insert(0, (str(a.video), str(a.script), *([str(a.dane)] if a.dane else [])))
    if not filmy:
        sys.exit("błąd: podaj --video i --script albo co najmniej jedno --film WIDEO SCENARIUSZ [DANE]")
    for f in filmy:
        if not 2 <= len(f) <= 3 or not all(Path(x).is_file() for x in f):
            sys.exit(f"błąd: --film wymaga istniejących plików WIDEO SCENARIUSZ [DANE]: {f}")

    repo = Path(__file__).resolve().parent
    PLIK_JOBA.parent.mkdir(parents=True, exist_ok=True)
    PLIK_JOBA.write_text(str(os.getpid()))
    serwer = postaw(a.obraz)
    host = adres(serwer)
    udalo_sie = False
    try:
        czekaj_na_gotowosc(host)
        ssh(host, "mkdir -p /root/scripts")
        rsync_do(host, f"{repo}/", f"root@{host}:/root/scripts/")
        for f in filmy:
            nazwa = Path(f[1]).stem
            katalog = f"/root/praca/{nazwa}"
            # work/ zakłada dopiero C1, ale `tee` loguje od pierwszego kroku — katalog musi już być
            ssh(host, f"mkdir -p {katalog}/work")
            for plik in f:
                rsync_do(host, plik, f"root@{host}:{katalog}/", "--progress")
            cel = a.work / nazwa if len(filmy) > 1 else a.work
            cel.mkdir(parents=True, exist_ok=True)
            belka = "BELKA:" in Path(f[1]).read_text(encoding="utf-8")
            dane = f"{katalog}/{Path(f[2]).name}" if len(f) > 2 else None
            for etap, polecenie in kroki_filmu(a, katalog, f"{katalog}/{Path(f[0]).name}",
                                               f"{katalog}/{Path(f[1]).name}", dane, belka):
                print(f"\n── {nazwa}: {etap} ──")
                wynik = ssh(host, f"cd {katalog} && {polecenie} 2>&1 | tee -a {katalog}/work/log.txt; "
                                  f"exit ${{PIPESTATUS[0]}}")
                # G8: log i lekkie wyniki po każdym kroku, żeby przy awarii nie zniknęły z maszyną
                rsync_do(host, f"root@{host}:{katalog}/work/", f"{cel}/", *LEKKIE)
                if wynik.returncode != 0:
                    raise RuntimeError(f"{nazwa}: {etap} nie powiodło się")
            rsync_do(host, f"root@{host}:{katalog}/work/", f"{cel}/")
            print(f"\nOK: {nazwa} → {cel}")
        udalo_sie = True
    finally:
        PLIK_JOBA.unlink(missing_ok=True)
        if udalo_sie or not a.keep_on_error:
            skasuj(serwer)
        else:
            print(f"\nmaszyna ZOSTAJE do diagnozy (watchdog skasuje ją po 58 min): "
                  f"ssh -i {KLUCZ} root@{host}\nskasuj: python3 scripts/worker.py down")


def main() -> None:
    ap = argparse.ArgumentParser(description="G3 — worker on-demand")
    pod = ap.add_subparsers(dest="cmd", required=True)
    pod.add_parser("up", help="postaw maszynę")
    pod.add_parser("down", help="skasuj maszynę")
    p_reap = pod.add_parser("reap", help="watchdog kosztów")
    p_reap.add_argument("--older-than", type=float, default=1.0, help="wiek w godzinach")
    p_snap = pod.add_parser("snapshot", help="G3b: obraz środowiska")
    p_snap.add_argument("akcja", choices=["build", "list", "promote", "prune"])
    p_snap.add_argument("id", nargs="?", type=int)
    p_job = pod.add_parser("job", help="pełny cykl C1–C12")
    p_job.add_argument("--work", required=True, type=Path, help="katalog na wynik (lokalnie)")
    p_job.add_argument("--video", type=Path)
    p_job.add_argument("--script", type=Path)
    p_job.add_argument("--film", nargs="+", action="append", metavar="PLIK",
                       help="WIDEO SCENARIUSZ [DANE]; można powtórzyć dla kilku filmów")
    p_job.add_argument("--obraz", default="produkcja", help="produkcja | kandydat | czysty | ID snapshotu")
    p_job.add_argument("--intro", action="store_true", help="3 s identyfikacji marki na początku")
    p_job.add_argument("--dane", type=Path, help="JSON z danymi do grafik (C7); bez niego krok pomijamy")
    p_job.add_argument("--kolor", choices=["czysty", "kinowy", "pastelowy"],
                       help="styl C6 zatwierdzony na podglądzie; bez niego powstaje tylko kolor-podglad.jpg")
    p_job.add_argument("--model", default="large-v3")
    p_job.add_argument("--keep-on-error", action="store_true", default=True)
    a = ap.parse_args()

    if a.cmd == "up":
        serwer = postaw(os.environ.get("YT_OBRAZ", "produkcja"))
        czekaj_na_gotowosc(adres(serwer))
        print(f"gotowe: ssh -i {KLUCZ} root@{adres(serwer)}")
    elif a.cmd == "down":
        skasuj()
    elif a.cmd == "reap":
        reap(a.older_than)
    elif a.cmd == "snapshot":
        if a.akcja == "build":
            snapshot_build()
        elif a.akcja == "promote":
            if not a.id:
                sys.exit("błąd: podaj ID snapshotu")
            snapshot_promote(a.id)
        elif a.akcja == "prune":
            snapshot_prune()
        else:
            for i in obrazy():
                print(f"{i['id']}  {i['labels'].get('status', '?'):10}  {i['image_size'] or 0:.1f} GB  "
                      f"{i['description']}")
    else:
        job(a)


if __name__ == "__main__":
    main()
