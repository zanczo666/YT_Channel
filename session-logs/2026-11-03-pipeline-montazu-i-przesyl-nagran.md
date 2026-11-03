---
kind: handoff
date: 2026-11-03
topic: pipeline-montazu-i-przesyl-nagran
status: in-progress
---

# Pipeline montażu C1–C9 na workerze on-demand, przesył nagrań Syncthingiem i wnioski z CapCut/Remotion

## Summary
Sesja 2026-11-02 → 11-03. Zbudowany cały łańcuch montażu od surowego nagrania do napisów i rozdziałów,
uruchamiany na workerze on-demand w Hetznerze. Pierwsze prawdziwe nagranie wyciągnęło dwa błędy i uwagę
właściciela o „sztywnym montażu" — poprawione. Zbudowany B3 (automatyczny przesył nagrań): Syncthing po
tailnecie, bez jednego portu publicznego, plus odbiornik przenoszący kompletne pliki do `inbox/`. Na koniec
analiza dwóch filmów o łączeniu Claude Code z CapCutem — z konkretnym wnioskiem, który odblokowuje C6.

## Key takeaways / decisions
- **Montaż jest po odcinku, nie jednym grafem filtrów.** Pierwsza wersja `cut.py` budowała jedną gałąź `trim`
  na sklejkę — przy ośmiu odcinkach 720p FFmpeg wywrócił serwer (OOM, 2026-11-02). Renderowanie po kawałku
  i sklejanie demukserem `concat` ma zużycie pamięci **stałe**, niezależne od liczby sklejek. Film na ~100 zdań
  inaczej nie przejdzie na żadnej maszynie.
- **Płynność sklejek** (uwaga właściciela po pierwszym montażu: „sztywny, brak płynności"): oddech na stykach,
  naprzemienne delikatne przybliżenie 1.07 (sąsiednie ujęcia nigdy nie mają tego samego kadru, więc cięcie
  czyta się jako zamierzone), 20 ms wygaszenia dźwięku na stykach. Kadr ucinany bardziej od dołu (`KADR_GORA`
  = 0.35), żeby oczy zostały w górnej tercji.
- **Nasze C3 jest mocniejsze od cudzego wycinania złych ujęć.** `align.py` porównuje transkrypcję ze
  **scenariuszem** — wie, co miało paść. Rozwiązania z YouTube zgadują wpadkę z pauzy i powtórzenia w samej
  transkrypcji, więc mylą wpadkę z celowym powtórzeniem retorycznym.
- **B3 — przesył po tailnecie, nie po internecie.** Tailscale był już na wszystkich urządzeniach, więc
  Syncthing dostał wyłączone globalAnnounce/localAnnounce/relays/NAT i nasłuch tylko na adresie tailnetu.
  `ufw` i tak przepuszcza wyłącznie `tailscale0`. Zero portów publicznych.
- **Foldery są `receiveonly`,** a `odbierz.py` **przenosi** pliki do `inbox/` twardym łączem (`os.link`) —
  żeby pipeline i Syncthing nie biły się o te same pliki i żeby skasowanie nagrania w telefonie nie skasowało
  materiału na serwerze.
- **Bramką jest nazwa pliku, nie długość nagrania** (propozycja właściciela, lepsza od mojej). W `DCIM/Camera`
  są prywatne filmy `VID*`; wzorce ignorowania przepuszczają wyłącznie `yt*.mp4`, a właściciel zmienia nazwę
  po nagraniu. Dlatego `MIN_CZAS_S = 0` — próg długości odrzucałby teraz celowo krótki materiał.
- **Kompletność pliku poznajemy po stabilności,** nie po nazwie: Syncthing pisze do `.syncthing.*.tmp`
  i zmienia nazwę atomowo, ale OBS pisałby prosto do folderu pod docelową nazwą. Stąd okno 45 s bez zmiany
  rozmiaru i mtime. Androidowe `.pending-*` (nagranie w trakcie zapisu) i `.trashed-*` (kosz galerii) kończą
  się na `.mp4`, więc filtr po rozszerzeniu ich nie łapie — są na liście pomijanych jawnie.
- **CapCut: nie bierzemy.** Nie ma publicznego API; „integracja" z pierwszego filmu zabija proces CapCuta,
  pisze do nieudokumentowanego `draft_content.json` i restartuje go AppleScriptem (macOS/Windows). Autor
  drugiego filmu mówi wprost, że **integracji nie ma** — przeciąga wygenerowane pliki do GUI ręcznie.
- **Z tych filmów bierzemy cztery rzeczy:** (1) LUT jako plik `.cube` + FFmpeg `lut3d` — sprawdzone, filtr jest
  w naszej instalacji, to odblokowuje C6; (2) animowane grafiki jako sekwencja klatek z Pillow (3 s @ 30 fps
  = 90 PNG) zamiast statycznego PNG — prawdziwa odpowiedź na „sztywny montaż", bez Remotion i Node'a;
  (3) plansze sekcji z tytułów rozdziałów C9 (dziś są tylko metadanymi YouTube); (4) zakreślacz na zrzucie
  publikacji przez Tesseract + Pillow. **Odrzucone:** b-roll z AI (podkopuje wiarygodność kanału o tradingu),
  Remotion (ciężka zależność Node + headless Chrome), hack z licznikiem SRT do przyspieszeń.
- **C6 musi zapisywać klatkę przed/po do zatwierdzenia** — „pastelowy, kinematyczny" to gust, nie matematyka.
- **Dźwięk:** telefon stoi daleko, więc rozsądniejsze są słuchawki jako mikrofon, ale profil HFP/SCO to 8/16 kHz
  mono wobec 48 kHz z mikrofonu telefonu. Pogłosu pomieszczenia C5 nie naprawi. Decyzja odłożona do pomiaru
  15-sekundowej próbki (poziom, pogłos, pasmo).
- **Gemini: modele się przestawiły.** `gemini-flash-latest` zwraca 503, `gemini-2.5-*` → 404, `gemini-pro-latest`
  → 429; działa **`gemini-3.5-flash`**. Doszły ponowienia z narastającym odstępem — drugi film przeszedł dopiero
  za szóstym podejściem, bez nich analiza przepadłaby w całości.

## State
- ✅ done:
  - **C1–C9**: `ingest.py`, `transcribe.py`, `align.py`, `cut.py`, `audio_master.py`, `graphics.py`,
    `subtitles.py`, `chapters.py`, wspólny limiter pamięci `proc.py`.
  - **Worker on-demand**: `scripts/worker.py` (tworzenie, przebieg, odbiór, kasowanie) — G3, G3a, G7, G8.
  - **B3**: Syncthing na serwerze (`~/.config/syncthing/config.xml`, foldery `yt-telefon`, `yt-komputer`,
    oba `receiveonly`), `scripts/odbierz.py` + `odbierz-nagrania.{service,timer}` (co minutę), `docs/SYNC.md`.
  - **Telefon sparowany i połączony bezpośrednio po tailnecie** (`ZORQGJE … 100.88.109.84:22000 tcp-server`),
    folder `yt-telefon` spięty, stan `idle`, zero błędów.
  - `yt_watch.py` z ponowieniami; `docs/research/2026-11-03-capcut-remotion.md`.
- 🔄 in progress:
  - **Właściciel wysłał pierwszy plik z telefonu tuż przed końcem sesji — niesprawdzony.** To pierwsza rzecz
    do zrobienia w nowej sesji (patrz „Next step").
- ⛔ waiting for (właściciel):
  - **Device ID komputera** — bez niego `yt-komputer` nie ma z kim się sparować.
  - Poziome nagranie próbne do pełnego przebiegu C1–C9.
  - Decyzja o mikrofonie (po pomiarze próbki).
  - Starsze: Discord (bot + token), konto marki YouTube, polityka prywatności na quantinvest.co,
    wklejenie poleceń w sesjach źródłowych (`docs/N8N_EXPORT_INSTRUKCJA.md`, `docs/MQL5_EXPORT_INSTRUKCJA.md`).

## Artifacts
- Skrypty pipeline'u: `scripts/{ingest,transcribe,align,cut,audio_master,graphics,subtitles,chapters,proc}.py`.
- Worker i przesył: `scripts/worker.py`, `scripts/odbierz.py`.
- Dokumenty: `docs/PIPELINE.md` (B3 na ✅), `docs/SYNC.md`, `docs/EDITING_RULES.md`,
  `docs/research/2026-11-03-capcut-remotion.md`.
- Poza repo, na serwerze:
  - `~/.config/syncthing/config.xml` — GUI `100.69.173.24:8384` (użytkownik `claude`, hasło w
    `~/.config/yt_channel/syncthing_gui_password`), nasłuch `tcp://` + `quic://100.69.173.24:22000`.
  - Device ID serwera: `STMWVBE-JL5RCRV-KCYPS35-B53Z6P3-O5FZVY7-SMT5AOX-SIDJ6TX-7OHE2QJ`.
  - Device ID telefonu: `ZORQGJE-XWE4HBF-7DMTBHX-SQIJSOB-LU5VQYZ-QZ2AP4B-LXPGA2K-5RTTJAU`.
  - `~/.config/systemd/user/syncthing.service.d/tailnet.conf` — `ExecStartPre` czeka na adres tailnetu
    (inaczej Syncthing wstaje przed `tailscaled` i nie ma na czym nasłuchiwać).
  - `~/.config/systemd/user/odbierz-nagrania.{service,timer}` — oba włączone.
  - `~/sync/{telefon,komputer}` (odbiór Syncthinga) → `~/inbox/` (wejście pipeline'u);
    stan odbiornika: `~/.local/state/yt_channel/odbierz.{json,log}`.
- Sekrety (600, nigdy nie wypisywać): `~/.config/yt_channel/{hetzner_api_token,gemini_api_key,youtube_api_key,syncthing_gui_password}`,
  klucz SSH `~/.ssh/yt_worker`.
- Git: gałąź sesji `claude/pickup-23f258`, scalona do `main`; `main` = `origin/main`.

## Next step
1. **Sprawdzić pierwszy plik z telefonu** — czy doszedł do `~/sync/telefon`, czy `odbierz.py` przeniósł go
   do `~/inbox/`, i czy **nie przyszło nic poza nim** (to jedyny prawdziwy test bramki `yt*.mp4`; dopóki nie
   było żadnego pasującego pliku, `globalFiles = 0` nie odróżniało „filtr działa" od „filtr odcina za dużo").
   W `~/inbox/` leży już `VID_20261102_230225.mp4` z ręcznego testu — nowy plik powinien dojść obok niego.
2. Device ID komputera → dopisać przez REST API, udostępnić `yt-komputer`, OBS pisze prosto do folderu (Send Only).
3. C6 przez `lut3d` z klatką przed/po; potem animowane sekwencje klatek w C7 i plansze sekcji z rozdziałów C9.
4. Zmienić domyślny model w `yt_watch.py` na `gemini-3.5-flash` (domyślny `gemini-flash-latest` zwraca 503).
5. Na koniec etapu: włączyć timer `worker.py reap --older-than 1` (G7 — napisany, nie zainstalowany).

## What NOT to do
- Nie wracać do jednego grafu filtrów w `cut.py` — to był OOM, który położył serwer.
- Nie instalować Remotion ani Node'a na workerze dla grafik, które Pillow robi sam.
- Nie generować b-rollu AI — na kanale o systematycznym tradingu podkopuje dokładnie tę wiarygodność,
  którą kanał ma budować. Liczby publiczne wyłącznie z Ledgera i kart fabryki.
- Nie luzować wzorców ignorowania w telefonie — w `DCIM/Camera` są prywatne filmy właściciela.
- Nie kopiować plików z `~/sync/` zamiast przenosić: pipeline i Syncthing nie mogą dzielić tych samych plików.
- Nie używać `/ralph-loop` (plugin nieaktualny). Nie pobierać cudzych napisów `yt-dlp` — do analiz `yt_watch.py`.
- Nie czytać ani nie zmieniać niczego w `MQL5_Freelancer` i `N8N_EA_System` poza tym, na co pozwala CLAUDE.md.
