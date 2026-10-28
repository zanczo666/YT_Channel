---
kind: handoff
date: 2026-10-29
topic: strategia-i-pipeline-kanalu
status: in-progress
---

# Zdefiniowanie kanału (strategia, opakowanie, miniatury, scenariusze) i architektura automatycznej produkcji

## Summary
Sesja 2026-10-20 → 10-29. Zdefiniowaliśmy tożsamość i strategię kanału, kontrakt contentowy z fabryką EA,
standard publikacji oparty na researchu 10 kanałów (YouTube Data API), generator miniatur (0 zł, z twarzą
właściciela), agentów `yt-scriptwriter` i `yt-producer`, a na końcu architekturę produkcji „Ty nagrywasz,
reszta automatycznie” (`docs/PIPELINE.md`). Następny krok: etap 1 (MVP montażu na VPS).

## Key takeaways / decisions
- **Kanał EN + napisy PL**, marka osobista „Imię Nazwisko — Systematic Trading Research”, **QuantInvest = „my research lab”**.
  Nagrywanie hybrydowe (twarz w hooku/CTA/werdykcie, środek ekran). 5–8 h/tydz., 1 film/tydz. Szczegóły: `docs/CHANNEL_STRATEGY.md`.
- **Teza:** pokazujemy lejek i odrzuty („test whether claims survive”). Research potwierdził: w niszy najlepiej
  działają sceptyczne testy z twardą liczbą (Algovibes, Part Time Larry, Ben Felix „paper jako bohater”).
- **Zero języka sprzedaży o sobie** w fazie zaufania (kilka–kilkanaście mies.): bez „we sell/buy/our product…”;
  o innych wolno („they sell”). CTA tylko niesprzedażowe. Słowo „AI” nigdy w tytule.
- **70% filmów = zdarzenia z projektów**, 30% evergreen; formuła: co się stało → dlaczego dotyczy widza → jak
  sprawdzić u siebie → werdykt. Liczby wyłącznie z Ledgera/kart, nigdy ilustracyjne.
- **Kontrakt z fabryką:** fabryka pisze karty do `N8N_EA_System/export/yt/` (lessons/funnel/graveyard,
  `publish_after` = embargo 2–4 tyg.); YT czyta TYLKO ten folder przez `git show` w `sync_context.py`
  (tryb `export_dir`) → `context/factory/`. Deny Read na N8N zostaje.
- **Miniatury: opcja 1 (0 zł)** — `thumbnail.py` (simple / rich: karta z panelem backtestu IS/OOS, odznaka ✓/✗/?,
  poświata twarzy), prawdziwe zdjęcia + lokalne wycinanie tła (rembg). **Generowanie AI wyłączone** —
  Gemini image nie ma darmowego limitu (HTTP 429); wracamy po 5–10 filmach na danych z A/B.
- **Scenariusz pisze Claude** (`yt-scriptwriter`): każde zdanie = wiersz z ID `L001…` (EN | PL | Na ekranie) —
  ten plik to teleprompter, źródło napisów EN/PL, beat mapa („one idea, one graphic”) i wzorzec do montażu.
- **Montaż: opcja A** — serwer robi transkrypcję (faster-whisper), dopasowanie do ID zdań, cięcie, dźwięk
  (−14 LUFS), napisy, render 1080p, QC. Wnioski z 4 filmów o automatyzacji montażu: nigdy jednym promptem,
  transkrypcja słowo po słowie = rdzeń, pętla notatki → reguły (`docs/EDITING_RULES.md`), grafiki jako szablony
  (pełna automatyzacja grafik = setki mln tokenów/film).
- **Decyzje pipeline (2026-10-29):** 2 bramki akceptacji (scenariusz + podgląd prywatny); render na
  `claudecore` **bez limitu CPU, tylko `MemoryMax` + nice** (na VPS ~kilkanaście sesji Claude Code, ~5/7 GB RAM);
  przesył **Syncthing** (telefon i komputer z OBS → `inbox/`); powiadomienia/akceptacje **Discord** (bot na VPS, przyciski).
- **Ograniczenia YouTube API:** upload z niezweryfikowanego projektu = **wymuszony prywatny** do audytu → wniosek
  o audyt na starcie (wymaga polityki prywatności na quantinvest.co); plansze końcowe, karty, przypięcie
  komentarza, Test & Compare — tylko ręcznie w Studio (~5 min/film).

## State
- ✅ done: strategia, standard publikacji, research kanałów, `sync_context` export_dir (test na sztucznych repo),
  instrukcje dla sesji N8N i MQL5, agenci + komendy (`/scenariusz`, `/publikacja`, `/pomysly`), miniatury
  (simple/rich, siatka, motywy equity/świece/lejek), zdjęcia twarzy wycięte (`assets/face/face-*.png`),
  `yt_research.py`, `yt_watch.py` (Gemini, pełna treść filmu), `docs/PIPELINE.md` z decyzjami.
- 🔄 in progress: etap 1 pipeline — **nic jeszcze nie zbudowane** (FFmpeg niezainstalowany na VPS).
- ⛔ waiting for (właściciel):
  - nagranie próbne 1–2 min (hook z celową pomyłką i powtórzeniem) — do testu montażu;
  - Discord: prywatny serwer + aplikacja bota (token → `~/.config/yt_channel/`);
  - Syncthing na telefonie i komputerze;
  - konto marki YouTube + weryfikacja telefonu;
  - kto zarządza quantinvest.co (polityka prywatności do audytu API);
  - wklejenie poleceń w sesjach źródłowych: `docs/N8N_EXPORT_INSTRUKCJA.md`, `docs/MQL5_EXPORT_INSTRUKCJA.md`
    (fabryka nie ma jeszcze `export/yt/`, freelance nie ma kart `VIDEO.md`).

## Artifacts
- Dokumenty: `docs/CHANNEL_STRATEGY.md`, `docs/YT_PUBLISHING_STANDARD.md`, `docs/PIPELINE.md`, `docs/EDITING_RULES.md`,
  `docs/research/2026-10-yt-kanaly.md`, `docs/templates/{script,description}-template.md`, `docs/export-yt-templates/`,
  `docs/N8N_EXPORT_INSTRUKCJA.md`, `docs/MQL5_EXPORT_INSTRUKCJA.md`.
- Analizy: `content/ideas/2026-10-21-{analiza-sesji-chatgpt,plan-startowy}.md`,
  `content/ideas/2026-10-28-analiza-miniatury-higgsfield.md`, `content/ideas/2026-10-29-analiza-automatyzacja-montazu.md`.
- Skrypty: `scripts/{sync_context,yt_research,yt_watch,thumbnail,thumbnail_grid,face_cutout}.py`.
- Agenci/komendy: `.claude/agents/{yt-producer,yt-scriptwriter}.md`, `.claude/commands/{publikacja,scenariusz,pomysly}.md`.
- Assets (poza git, `.gitignore`): `assets/face/{raw,cut}/`, `assets/face/face-{neutral,skeptic,squint,pass}.png`;
  przykłady miniatur `content/publish/_przyklad/`.
- Sekrety (poza repo, 600): `~/.config/yt_channel/youtube_api_key`, `~/.config/yt_channel/gemini_api_key`
  (projekt Google Cloud `yt-channel-research-513011`, klucze ograniczone do IP VPS 62.238.52.244 + 2a01:4f9:c015:6aea::/64).
- Środowisko: venv `/home/claude/.venvs/rembg` (rembg 2.0.86); Pillow w user site (skrypty z Pillow uruchamiać `python3`, nie `python3 -I`).
- Git: `main` = `772ba74`, **12 commitów przed `origin/main` — niewypchnięte**. Główny katalog przełączony na `main`.

## Next step
Zacząć etap 1 z `docs/PIPELINE.md`: `sudo apt install ffmpeg`, venv z `faster-whisper`, potem
`scripts/` dla C1→C3 (ingest, transkrypcja słowo po słowie, dopasowanie do ID zdań scenariusza). Równolegle
napisać scenariusz filmu #2 (`/scenariusz validation-gates-1 2`) — test całości, gdy przyjdzie nagranie próbne.

## What NOT to do
- Nie generować miniatur AI (brak darmowego limitu, decyzja: opcja 1 do czasu oceny).
- Nie używać `/ralph-loop` (plugin nieaktualny — w pamięci projektu).
- Nie pobierać napisów cudzych filmów `yt-dlp` (ToS, ryzyko blokady IP VPS) — do analiz `yt_watch.py` (Gemini).
- Nie montować „jednym promptem” ani nie generować grafik od zera per film (koszt tokenów) — szablony.
- Nie zakładać limitu CPU — tylko pamięć (decyzja użytkownika + ochrona sesji Claude Code).
- Nie czytać plików `N8N_EA_System` poza kopią `export/yt/` przez skrypt.
