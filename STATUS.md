# STATUS — YT_Channel

_Ostatnia aktualizacja: 2026-11-03_

## Stan
- **Następny etap:** poziome nagranie próbne → pełny przebieg C1–C9 na workerze; potem C6 (LUT) i animacje w C7.
- **Pipeline montażu C1–C9 działa** (`docs/PIPELINE.md`): ingest, transkrypcja, dopasowanie do scenariusza,
  cięcie + EDL, mastering dźwięku, grafiki, napisy EN/PL, rozdziały. C6 (korekcja barwna) nadal 🟡.
- **Worker on-demand w Hetznerze** (`scripts/worker.py`): tworzenie, przebieg, odbiór wyniku, kasowanie.
  Timer `reap` dla osieroconych workerów — napisany, **nie zainstalowany** (świadomie, na koniec etapu).
- **B3 — przesył nagrań gotowy** (`docs/SYNC.md`): Syncthing po tailnecie (zero portów publicznych),
  foldery `receiveonly`, `scripts/odbierz.py` + timer co minutę przenosi kompletne pliki do `inbox/`.
  Telefon sparowany i połączony bezpośrednio; bramka `yt*.mp4` (reszta materiału z `DCIM/Camera` pomijana).
  **Komputer jeszcze nie sparowany** — brakuje jego Device ID.
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
- 2026-11-02→03 — Pipeline montażu C1–C9 na workerze on-demand (`scripts/worker.py`); poprawki płynności
  sklejek po uwadze właściciela („sztywny, brak płynności"); B3: Syncthing po tailnecie + `odbierz.py`
  (telefon sparowany, bramka `yt*.mp4`, `docs/SYNC.md`); ponowienia w `yt_watch.py` (model bywa przeciążony);
  analiza dwóch filmów o CapCut/Remotion → `docs/research/2026-11-03-capcut-remotion.md` (bierzemy LUT `.cube`
  do C6, animowane sekwencje klatek i plansze sekcji do C7; odrzucamy b-roll z AI, Remotion i CapCuta).
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
- Sprawdzić pierwszy plik przesłany z telefonu: czy doszedł do `~/sync/telefon`, czy `odbierz.py` przeniósł
  go do `inbox/` i czy nie przyszło nic poza nim (bramka `yt*.mp4`).
- Device ID komputera → sparować folder `yt-komputer`, OBS pisze prosto do niego (Send Only).
- Poziome nagranie próbne → pełny przebieg C1–C9 z `--dane` dla grafik.
- C6 przez FFmpeg `lut3d` (z klatką przed/po do zatwierdzenia — LUT to gust, nie matematyka).
- C7: animowane sekwencje klatek z Pillow zamiast statycznych PNG + plansze sekcji z rozdziałów C9.
- Prerekwizyty w źródłach: `docs/OVERVIEW.md` w obu projektach, karty `mql5/<Nazwa>/VIDEO.md` we freelance,
  trailer `Content: yes` w commitach N8N_EA_System.
- Pierwsze uruchomienie interaktywne `claude` (zaufanie do folderu + import OVERVIEW.md) i testy granic.
- Instancja Remote Control `claude-rc@YT_Channel` (bez `--spawn worktree`).
- Prywatne repo na GitHub + push.
