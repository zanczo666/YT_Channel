# TODO — YT_Channel

## Do zrobienia
- [ ] Po 5–10 filmach: ocena miniatur AI (opcja 2 — Gemini API z płatnościami i alertem budżetu) na podstawie testów A/B.
- [ ] Po kilku testach A/B: zatwierdzić miniaturę-matkę → `assets/style/master.jpg`.
- [ ] Wgrać 3–5 zdjęć twarzy do `assets/face/` (opis w `assets/face/README.md`) — potrzebne do miniatur.
- [ ] Po założeniu kanału: sprawdzić w YouTube Studio Test & Compare (tytuły/miniatury) i zasady hashtagów.
- [ ] Research kanałów — odświeżenie 2027-01 (`scripts/yt_research.py`).
- [ ] **Fabryka (z sesji N8N, nie stąd):** wkleić polecenie z `docs/N8N_EXPORT_INSTRUKCJA.md` → folder `export/yt/`
      + sekcja „Eksport dla kanału YT” w ich CLAUDE.md.
- [ ] **Fabryka:** Research Ledger z ID `QF-xxx` i powodem odrzutu na każdym etapie.
- [ ] **Fabryka:** zapisywanie źródła publikacji (autorzy, tytuł, rok) dla każdej strategii.
- [ ] **Fabryka:** pierwszy miesięczny raport `export/yt/funnel/RRRR-MM.md` (tylko realne liczby).
- [x] Kanał: ostateczna nazwa „Radoslaw Lubas - Systematic Trading Lab”
- [ ] Kanał: baner, awatar i opis do zatwierdzenia (`docs/CHANNEL_SETUP.md`), bez QuantInvest do odwołania.
- [ ] Strona QuantInvest: sekcje Methodology (bramki v1.0) i Research Ledger (także odrzuty).
- [ ] Newsletter z miesięcznym raportem lejka (wybór darmowego narzędzia).
- [ ] Filmy bez zależności od fabryki: #1 intro, #2 Validation Gates #1, #5 Tools (`content/ideas/2026-10-21-plan-startowy.md`).
- [ ] Globalny `~/.claude/CLAUDE.md` nadal wymaga `/ralph-loop` — plugin nieaktualny; usunąć regułę (decyzja użytkownika).
- [ ] `docs/OVERVIEW.md` (≤60 linii) w MQL5_Freelancer — wykonać z sesji tego projektu.
- [ ] `docs/OVERVIEW.md` (≤60 linii) w N8N_EA_System — wykonać z sesji tego projektu.
- [ ] Karty `mql5/<Nazwa>/VIDEO.md` we freelance (polecenie: `docs/MQL5_EXPORT_INSTRUKCJA.md`) dla narzędzi do pokazania (IchimokuProPanel,
      RiskPositionSizeCalculator, SessionSpreadAlert, SpreadMonitorScalpers).
- [ ] Linia do `CLAUDE.md` freelance: przy publikacji narzędzia utwórz/zaktualizuj `VIDEO.md`.
- [ ] Linia do `CLAUDE.md` N8N: trailer `Content: yes` + „Lekcja: …" dla ciekawych commitów.
- [ ] (opcjonalne, gdy wrócimy do sandboxa) Zainstalować `bubblewrap` + `socat`
      — `sudo apt install -y bubblewrap socat`; potem `sandbox.enabled:true` w settings.json.
- [ ] Przed produkcyjnym uruchomieniem instancji RC: przywrócić `sandbox.enabled:true`.
- [ ] Włączyć timer: `systemctl --user enable --now yt-sync.timer`.
- [ ] Pierwsze uruchomienie interaktywne `claude` + testy granic (krok 7 dokumentu).
- [ ] Sparować komputer w Syncthingu (potrzebne jego Device ID) → folder `yt-komputer`, OBS pisze prosto do niego.
- [ ] Sprawdzić pierwszy plik z telefonu: `~/sync/telefon` → `inbox/`, i czy bramka `yt*.mp4` nie przepuściła nic poza nim.
- [ ] Poziome nagranie próbne → pełny przebieg C1–C9 na workerze (`--dane` dla grafik).
- [ ] C6: korekcja barwna przez FFmpeg `lut3d` z pliku `.cube` + klatka przed/po do zatwierdzenia.
- [ ] C7: animowane sekwencje klatek (Pillow) zamiast statycznych PNG; plansze sekcji z rozdziałów C9.
- [ ] Zmierzyć dźwięk na 15-sekundowej próbce (poziom, pogłos, pasmo) przed decyzją o mikrofonie.
- [ ] Zmienić domyślny model w `yt_watch.py` — `gemini-flash-latest` zwraca 503; działa `gemini-3.5-flash`.
- [ ] G7: włączyć timer `worker.py reap --older-than 1` (na koniec etapu).
- [ ] Zawęzić 13 układów miniatur do 3.
- [ ] Uruchomić instancję Remote Control `claude-rc@YT_Channel` (bez worktree).

## W toku
- (nic)

## Ukończone
- [x] B3 — przesył nagrań: Syncthing po tailnecie, `scripts/odbierz.py` + timer, `docs/SYNC.md`; telefon sparowany.
- [x] Pipeline montażu C1–C9 + worker on-demand w Hetznerze (`scripts/worker.py`).
- [x] Ponowienia w `yt_watch.py` (model bywa przeciążony — bez nich długa analiza przepada).
- [x] Analiza CapCut/Remotion → `docs/research/2026-11-03-capcut-remotion.md`.
- [x] Research 10 kanałów przez YouTube Data API → `docs/research/2026-10-yt-kanaly.md`, `docs/YT_PUBLISHING_STANDARD.md`.
- [x] Agent `yt-producer` + `/publikacja`, generator miniatur `scripts/thumbnail.py`.
- [x] Strategia kanału: `docs/CHANNEL_STRATEGY.md`, szablony `docs/templates/`, `docs/export-yt-templates/`.
- [x] `sync_context.py`: tryb `export_dir` (lustro `export/yt/` → `context/factory/`, embargo, usunięcia) + test na sztucznych repo.
- [x] Analiza sesji ChatGPT i plan 10 filmów w `content/ideas/`.
- [x] Repo git (`main`) + struktura katalogów.
- [x] `CLAUDE.md`, `.claude/settings.json`, `.gitignore`.
- [x] `scripts/sync_context.py` + test lokalny.
- [x] Komenda `/pomysly`.
- [x] Pliki timera systemd `yt-sync.{service,timer}`.
