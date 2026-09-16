# TODO — YT_Channel

## Do zrobienia
- [ ] `docs/OVERVIEW.md` (≤60 linii) w MQL5_Freelancer — wykonać z sesji tego projektu.
- [ ] `docs/OVERVIEW.md` (≤60 linii) w N8N_EA_System — wykonać z sesji tego projektu.
- [ ] Karty `mql5/<Nazwa>/VIDEO.md` we freelance dla narzędzi do pokazania (IchimokuProPanel,
      RiskPositionSizeCalculator, SessionSpreadAlert, SpreadMonitorScalpers).
- [ ] Linia do `CLAUDE.md` freelance: przy publikacji narzędzia utwórz/zaktualizuj `VIDEO.md`.
- [ ] Linia do `CLAUDE.md` N8N: trailer `Content: yes` + „Lekcja: …" dla ciekawych commitów.
- [ ] (opcjonalne, gdy wrócimy do sandboxa) Zainstalować `bubblewrap` + `socat`
      — `sudo apt install -y bubblewrap socat`; potem `sandbox.enabled:true` w settings.json.
- [ ] Przed produkcyjnym uruchomieniem instancji RC: przywrócić `sandbox.enabled:true`.
- [ ] Włączyć timer: `systemctl --user enable --now yt-sync.timer`.
- [ ] Pierwsze uruchomienie interaktywne `claude` + testy granic (krok 7 dokumentu).
- [ ] Utworzyć prywatne repo GitHub, `git remote add origin …`, `git push -u origin main`.
- [ ] Uruchomić instancję Remote Control `claude-rc@YT_Channel` (bez worktree).

## W toku
- (nic)

## Ukończone
- [x] Repo git (`main`) + struktura katalogów.
- [x] `CLAUDE.md`, `.claude/settings.json`, `.gitignore`.
- [x] `scripts/sync_context.py` + test lokalny.
- [x] Komenda `/pomysly`.
- [x] Pliki timera systemd `yt-sync.{service,timer}`.
