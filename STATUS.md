# STATUS — YT_Channel

_Ostatnia aktualizacja: 2026-10-29_

## Stan
- **Następny etap:** etap 1 pipeline (MVP montażu na VPS) — `docs/PIPELINE.md`; czeka na nagranie próbne.
- **Strategia kanału gotowa:** `docs/CHANNEL_STRATEGY.md`; plan 10 filmów: `content/ideas/2026-10-21-plan-startowy.md`.
- **Przepływ z fabryki:** `sync_context.py` umie kopiować `export/yt/` → `context/factory/`; po stronie fabryki folder
  jeszcze nie istnieje (instrukcja: `docs/N8N_EXPORT_INSTRUKCJA.md`).
- Szkielet projektu założony: repo git (`main`), struktura katalogów, `CLAUDE.md`, `.claude/settings.json`.
- Skrypt synchronizacji kontekstu `scripts/sync_context.py` — gotowy, przetestowany lokalnie
  (opt-in VIDEO.md, tryb `Content: yes`, dedup, auto-commit; naprawiony bug `--since` z gołą datą).
- Komenda `/pomysly` gotowa.
- Timer systemd `yt-sync` (co 6h) — pliki unit przygotowane, składnia zwalidowana; **timer nie włączony**.
- **Sandbox WYŁĄCZONY** (`sandbox.enabled:false`) — decyzja tymczasowa. Reguły `deny` (Read/Edit) nadal
  chronią narzędzia Claude; znika twarda warstwa dla procesów z Basha. Wrócić do `true` przed produkcyjnym RC.
- `CLAUDE.md` wzmocniony sekcją „Projekty źródłowe — TYLKO ODCZYT (bezwzględnie)".

## Dziennik sesji
- 2026-10-21→29 — Research 10 kanałów (YouTube API) → standard publikacji; miniatury 0 zł (simple/rich, twarz
  właściciela, rembg); agenci `yt-scriptwriter`/`yt-producer`; analiza filmów przez Gemini (`yt_watch.py`);
  architektura produkcji `docs/PIPELINE.md` (2 bramki, render na claudecore, Syncthing, Discord). Handoff:
  `session-logs/2026-10-29-strategia-i-pipeline-kanalu.md`.
- 2026-10-21 — Zdefiniowano strategię kanału (EN + napisy PL, marka osobista + QuantInvest jako lab, nagrywanie
  hybrydowe, start za 0 zł, 70% projekty / 30% evergreen, 5 filarów, zero języka sprzedaży o sobie). Przeanalizowano
  sesję ChatGPT. Dodano kontrakt contentowy z fabryką (`export/yt/` → `context/factory/`, tryb `export_dir`).
- 2026-09-16 — Założono cały projekt YT_Channel (main, bez worktree): repo, struktura, CLAUDE.md,
  settings.json, sync_context.py + testy end-to-end, komenda /pomysly, unity systemd. Naprawiono bug
  okna `--since`. Użytkownik wyłączył sandbox (tymczasowo).

## W toku
- (nic)

## Następne kroki
- Prerekwizyty w źródłach: `docs/OVERVIEW.md` w obu projektach, karty `mql5/<Nazwa>/VIDEO.md` we freelance,
  trailer `Content: yes` w commitach N8N_EA_System.
- Pierwsze uruchomienie interaktywne `claude` (zaufanie do folderu + import OVERVIEW.md) i testy granic.
- Instancja Remote Control `claude-rc@YT_Channel` (bez `--spawn worktree`).
- Prywatne repo na GitHub + push.
