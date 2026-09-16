---
kind: handoff
date: 2026-09-16
slug: zalozenie-projektu
topic: Założenie projektu YT_Channel (main, bez worktree)
---

# Handoff — Założenie projektu YT_Channel

## Cel sesji
Założyć od zera cały projekt `YT_Channel` (trzeci projekt Claude Code / Remote Control) — technicznie:
prosta kontrola wersji na `main` bez worktree, niezawodne i bezpieczne czytanie z dwóch projektów
źródłowych (`MQL5_Freelancer`, `N8N_EA_System`), które projekt ma **tylko czytać**. Treść kanału później.

## Co zrobiono (zakończone)
- Repo git (`main`) + struktura: `.claude/{commands}`, `scripts/`, `context/{feed,tools}`, `content/{ideas,scripts}`.
- `CLAUDE.md` — importy `@OVERVIEW.md` obu źródeł, granice treści, konwencje, sekcja „TYLKO ODCZYT (bezwzględnie)".
- `.claude/settings.json` — uprawnienia (`deny` Edit/Read na źródłach, sekrety) + sandbox.
- `scripts/sync_context.py` — sync bez LLM: freelance opt-in przez `mql5/<Nazwa>/VIDEO.md`,
  N8N tylko commity `Content: yes` (przez `git log --grep`, bez odczytu plików), dedup `.seen_commits`,
  auto-commit `context-sync:`. **Przetestowany end-to-end** na sztucznych repo (opt-in, dedup, przyrost).
- Komenda `/pomysly`. Unity systemd `yt-sync.{service,timer}` (co 6h, `flock`) — składnia zwalidowana.
- `STATUS.md`, `TODO.md`, `.gitignore`.
- **Naprawiony bug**: `--since` z gołą datą gubił commity z dnia ostatniej synchronizacji → pełny
  timestamp + 2-dniowy margines nakładki okna (commit `a18fed7`).

## Decyzje (ważne, nieoczywiste)
- **`main`, bez worktree** (decyzja użytkownika) — commit prosto na main, model prosty.
- **Freelance: opt-in przez `VIDEO.md`** zamiast nieistniejącego `codebase/` z pierwotnego dokumentu.
  Wolno czytać kod `mql5/`; twarda blokada `data/`, `session-logs/`.
- **N8N: pełna blokada odczytu** (klejnoty koronne: prompty generatora, strategie, Stripe, sekrety
  `.env`+`.mcp.json`). Do YT trafia wyłącznie feed z `Content: yes`.
- **Sandbox tymczasowo WYŁĄCZONY** (`enabled:false`, decyzja użytkownika „poki co"). Reguły `deny`
  (Read/Edit) nadal chronią narzędzia Claude; znika twarda warstwa dla procesów z Basha.

## Stan repo
- Gałąź bieżąca: `claude/zamknij-sesje-2026-09-16-zalozenie-projektu` (scalona do `main`, `--no-ff`, `6604a4f`).
- `main`: `6604a4f` (merge) ← `db08ae7` ← `a18fed7` ← `ee4a25f`.
- Working tree czysty. **Brak remote `origin`** — praca tylko lokalnie, nic nie wypchnięte.

## Następne kroki (z TODO.md)
1. Utworzyć prywatne repo GitHub, `git remote add origin …`, `git push -u origin main` (PILNE — praca tylko na 1 dysku).
2. Prerekwizyty w źródłach (poza YT): `docs/OVERVIEW.md` w obu, karty `mql5/<Nazwa>/VIDEO.md` we freelance
   (IchimokuProPanel, RiskPositionSizeCalculator, SessionSpreadAlert, SpreadMonitorScalpers) + linie do ich `CLAUDE.md`.
3. (opcjonalnie) `bubblewrap`+`socat` i powrót do `sandbox.enabled:true` — przed produkcyjnym RC.
4. Włączyć timer: `systemctl --user enable --now yt-sync.timer`.
5. Pierwsze uruchomienie interaktywne `claude` (zaufanie do folderu + import OVERVIEW.md) + testy granic.
6. Instancja `claude-rc@YT_Channel` (bez `--spawn worktree`).

## Uwagi / pułapki
- Ścieżki bazowe wpisane jako `/home/claude/...` (tu `$HOME=/home/claude`). Na docelowym VPS o innej
  nazwie użytkownika podmienić ścieżki bezwzględne w `settings.json` i `CLAUDE.md` (nie działa `$HOME`).
- Katalogi `context/feed`, `context/tools`, `content/ideas`, `content/scripts` są puste → git ich nie
  śledzi; odtworzą się przy pierwszym sync / `/pomysly`.
- Plan wdrożenia: `~/.claude/plans/przeczytaj-plik-w-kt-rym-serene-ritchie.md`. Dokument źródłowy: `YT_Channel_setup.md`.
