#!/usr/bin/env python3
"""Synchronizacja kontekstu YT_Channel z projektów źródłowych — bez LLM.

Zbiera świeże zdarzenia z dwóch repozytoriów i zapisuje je do `context/`:

- MQL5_Freelancer: kopiuje karty `mql5/<Narzędzie>/VIDEO.md` do `context/tools/`
  (opt-in: bierzemy WYŁĄCZNIE narzędzia, które mają kartę VIDEO.md) i dopisuje do
  feedu commity dotykające tych narzędzi.
- N8N_EA_System: dopisuje do feedu WYŁĄCZNIE commity z trailerem `Content: yes`
  (czytane przez `git log --grep`, tylko metadane — bez odczytu plików repo).

Czyta zawsze z gałęzi `ref` (domyślnie `main`) przez `git -C … log/show/ls-tree`,
nie z katalogu roboczego źródła. Dedup po hashach commitów (`context/.seen_commits`).
Na końcu — jeśli powstały zmiany — commituje `context/` osobnym commitem `context-sync: …`.
"""

from __future__ import annotations

import datetime as _dt
import subprocess
import sys
from pathlib import Path

# --- Konfiguracja -----------------------------------------------------------

# Katalog projektu YT_Channel (dwa poziomy nad tym plikiem: scripts/ -> projekt).
PROJECT_ROOT = Path(__file__).resolve().parent.parent
CONTEXT_DIR = PROJECT_ROOT / "context"
FEED_DIR = CONTEXT_DIR / "feed"
TOOLS_DIR = CONTEXT_DIR / "tools"
SEEN_FILE = CONTEXT_DIR / ".seen_commits"
LAST_SYNC_FILE = CONTEXT_DIR / ".last_sync"
LOG_FILE = CONTEXT_DIR / ".sync.log"

# Ile dni wstecz przy pierwszym uruchomieniu (gdy brak .last_sync).
FIRST_RUN_DAYS = 30

# Margines nakładki okna przy kolejnych przebiegach (dni). Zapobiega gubieniu
# commitów z dnia ostatniej synchronizacji; duplikaty odsiewa `.seen_commits`.
OVERLAP_DAYS = 2

SOURCES = [
    {
        "name": "MQL5_Freelancer",
        "repo": Path("/home/claude/projects/MQL5_Freelancer"),
        "ref": "main",
        "mode": "video_cards",   # opt-in przez mql5/<Narzędzie>/VIDEO.md
        "tool_root": "mql5",     # katalog, w którym leżą narzędzia
    },
    {
        "name": "N8N_EA_System",
        "repo": Path("/home/claude/projects/N8N_EA_System"),
        "ref": "main",
        "mode": "flagged",       # tylko commity z trailerem Content: yes
        "flag_grep": r"Content: *yes",
    },
]

# --- Narzędzia pomocnicze ---------------------------------------------------


def log(msg: str) -> None:
    """Dopisuje wpis do logu i wypisuje na stdout."""
    stamp = _dt.datetime.now().isoformat(timespec="seconds")
    line = f"[{stamp}] {msg}"
    print(line)
    with LOG_FILE.open("a", encoding="utf-8") as fh:
        fh.write(line + "\n")


def git(repo: Path, *args: str, check: bool = True) -> str:
    """Uruchamia git w danym repo i zwraca stdout (pusty przy błędzie, gdy check=False)."""
    res = subprocess.run(
        ["git", "-C", str(repo), *args],
        capture_output=True,
        text=True,
    )
    if res.returncode != 0:
        if check:
            raise RuntimeError(f"git {' '.join(args)} @ {repo}: {res.stderr.strip()}")
        return ""
    return res.stdout


def repo_ready(repo: Path, ref: str) -> bool:
    """Sprawdza, że repo istnieje, jest gitem i ma gałąź `ref`."""
    if not (repo / ".git").exists():
        log(f"POMIJAM {repo}: to nie jest repozytorium gita")
        return False
    if not git(repo, "rev-parse", "--verify", ref, check=False).strip():
        log(f"POMIJAM {repo}: brak gałęzi '{ref}'")
        return False
    return True


def load_seen() -> set[str]:
    if SEEN_FILE.exists():
        return {ln.strip() for ln in SEEN_FILE.read_text(encoding="utf-8").splitlines() if ln.strip()}
    return set()


def save_seen(seen: set[str]) -> None:
    SEEN_FILE.write_text("\n".join(sorted(seen)) + "\n", encoding="utf-8")


def since_arg() -> str:
    """Zwraca wartość dla --since jako pełny timestamp 'RRRR-MM-DD HH:MM:SS'.

    Uwaga: gołej daty (`--since=2026-09-15`) NIE używamy — git rozwija ją względem
    bieżącej godziny i pomija commity z tego samego dnia. Dlatego zawsze podajemy
    czas. Przy kolejnych przebiegach cofamy się o OVERLAP_DAYS (dedup i tak chroni).
    """
    now = _dt.datetime.now()
    if LAST_SYNC_FILE.exists():
        val = LAST_SYNC_FILE.read_text(encoding="utf-8").strip()
        if val:
            try:
                last = _dt.datetime.fromisoformat(val)
                since = last - _dt.timedelta(days=OVERLAP_DAYS)
                return since.strftime("%Y-%m-%d %H:%M:%S")
            except ValueError:
                log(f"Niepoprawny .last_sync ('{val}') — traktuję jak pierwszy przebieg")
    since = now - _dt.timedelta(days=FIRST_RUN_DAYS)
    return since.strftime("%Y-%m-%d %H:%M:%S")


def feed_path(today: _dt.date) -> Path:
    """Plik feedu dla bieżącego tygodnia ISO: RRRR-Www.md."""
    iso_year, iso_week, _ = today.isocalendar()
    return FEED_DIR / f"{iso_year}-W{iso_week:02d}.md"


def append_feed(today: _dt.date, section_title: str, entries: list[str]) -> None:
    """Dopisuje sekcję do tygodniowego feedu (jeśli są wpisy)."""
    if not entries:
        return
    path = feed_path(today)
    header = ""
    if not path.exists():
        iso_year, iso_week, _ = today.isocalendar()
        header = f"# Feed {iso_year}-W{iso_week:02d}\n\n"
    with path.open("a", encoding="utf-8") as fh:
        fh.write(header)
        fh.write(f"## {today.isoformat()} — {section_title}\n")
        for e in entries:
            fh.write(e + "\n")
        fh.write("\n")


# --- Tryby źródeł -----------------------------------------------------------


def tools_with_cards(repo: Path, ref: str, tool_root: str) -> dict[str, str]:
    """Zwraca {nazwa_narzędzia: ścieżka_do_VIDEO.md} dla narzędzi mających kartę."""
    out = git(repo, "ls-tree", "-r", "--name-only", ref, "--", tool_root, check=False)
    result: dict[str, str] = {}
    for line in out.splitlines():
        line = line.strip()
        if line.endswith("/VIDEO.md"):
            # np. mql5/IchimokuProPanel/VIDEO.md -> IchimokuProPanel
            parts = line.split("/")
            if len(parts) >= 3:
                result[parts[-2]] = line
    return result


def sync_video_cards(src: dict, since: str, seen: set[str], today: _dt.date) -> list[str]:
    """MQL5_Freelancer: kopiuje karty VIDEO.md + feed z commitów narzędzi z kartą."""
    repo, ref, tool_root = src["repo"], src["ref"], src["tool_root"]
    cards = tools_with_cards(repo, ref, tool_root)
    if not cards:
        log(f"{src['name']}: brak kart VIDEO.md w '{tool_root}/' — nic do zebrania")
        return []

    # 1) Odśwież karty w context/tools/ (nadpisanie treścią z gałęzi ref).
    for tool, card_path in sorted(cards.items()):
        content = git(repo, "show", f"{ref}:{card_path}", check=False)
        if content:
            (TOOLS_DIR / f"{tool}.md").write_text(content, encoding="utf-8")
    log(f"{src['name']}: karty narzędzi: {', '.join(sorted(cards))}")

    # 2) Feed: nowe commity dotykające katalogów narzędzi, które mają kartę.
    tool_paths = [f"{tool_root}/{tool}" for tool in cards]
    raw = git(
        repo, "log", ref, f"--since={since}", "--no-merges",
        "--format=%H%x1f%s", "--", *tool_paths, check=False,
    )
    entries: list[str] = []
    for line in raw.splitlines():
        if "\x1f" not in line:
            continue
        h, subject = line.split("\x1f", 1)
        if h in seen:
            continue
        seen.add(h)
        entries.append(f"- `{h[:7]}` {subject}")
    return entries


def sync_flagged(src: dict, since: str, seen: set[str], today: _dt.date) -> list[str]:
    """N8N_EA_System: feed wyłącznie z commitów z trailerem Content: yes (tylko metadane)."""
    repo, ref = src["repo"], src["ref"]
    raw = git(
        repo, "log", ref, "-i", f"--grep={src['flag_grep']}",
        f"--since={since}", "--format=%H%x1f%s%x1f%b%x1e", check=False,
    )
    entries: list[str] = []
    for record in raw.split("\x1e"):
        record = record.strip("\n")
        if not record or "\x1f" not in record:
            continue
        parts = record.split("\x1f", 2)
        h = parts[0]
        subject = parts[1] if len(parts) > 1 else ""
        body = parts[2] if len(parts) > 2 else ""
        if h in seen:
            continue
        seen.add(h)
        entries.append(f"- `{h[:7]}` {subject}")
        for bl in body.splitlines():
            bl = bl.strip()
            if bl.lower().startswith("lekcja:"):
                entries.append(f"  - {bl}")
    return entries


# --- Auto-commit ------------------------------------------------------------


def autocommit(summary: str) -> None:
    """Commituje zmiany w context/ (bez plików ignorowanych) osobnym commitem."""
    status = git(PROJECT_ROOT, "status", "--porcelain", "context/", check=False).strip()
    if not status:
        log("Brak zmian w context/ — nic do commitu")
        return
    git(PROJECT_ROOT, "add", "context/")
    # Po dodaniu — sprawdź, czy cokolwiek jest zastage'owane (ignorowane pliki odpadają).
    staged = git(PROJECT_ROOT, "diff", "--cached", "--name-only", "context/", check=False).strip()
    if not staged:
        log("Po git add tylko pliki ignorowane — nic do commitu")
        return
    git(PROJECT_ROOT, "commit", "-m", f"context-sync: {summary}")
    log(f"Commit: context-sync: {summary}")


# --- Main -------------------------------------------------------------------


def main() -> int:
    FEED_DIR.mkdir(parents=True, exist_ok=True)
    TOOLS_DIR.mkdir(parents=True, exist_ok=True)

    today = _dt.date.today()
    since = since_arg()
    seen = load_seen()
    log(f"START sync (since={since})")

    total_new = 0
    summary_bits: list[str] = []
    for src in SOURCES:
        if not repo_ready(src["repo"], src["ref"]):
            continue
        try:
            if src["mode"] == "video_cards":
                entries = sync_video_cards(src, since, seen, today)
            elif src["mode"] == "flagged":
                entries = sync_flagged(src, since, seen, today)
            else:
                log(f"{src['name']}: nieznany tryb '{src['mode']}' — pomijam")
                continue
        except RuntimeError as exc:
            log(f"{src['name']}: BŁĄD — {exc}")
            continue

        title = src["name"] + (" (Content: yes)" if src["mode"] == "flagged" else "")
        append_feed(today, title, entries)
        if entries:
            n = sum(1 for e in entries if e.startswith("- `"))
            total_new += n
            summary_bits.append(f"{src['name']}:{n}")
            log(f"{src['name']}: {n} nowych wpisów do feedu")
        else:
            log(f"{src['name']}: 0 nowych wpisów")

    save_seen(seen)
    LAST_SYNC_FILE.write_text(
        _dt.datetime.now().isoformat(timespec="seconds"), encoding="utf-8"
    )

    summary = ", ".join(summary_bits) if summary_bits else "0 nowych zdarzeń"
    autocommit(summary)
    log(f"KONIEC sync ({total_new} nowych zdarzeń łącznie)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
