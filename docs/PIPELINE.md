# Architektura produkcji kanału — „Ty nagrywasz, reszta dzieje się sama”

_Wersja 1.0 — 2026-10-29. Dokument docelowy: co jest potrzebne, w jakiej kolejności to budujemy i gdzie
świadomie zostaje człowiek. Status elementów: ✅ gotowe, 🟡 częściowo, ⬜ do zbudowania._

## 1. Cel i uczciwe granice automatyzacji
**Cel:** Twoja rola = nagranie (sesja co 2 tygodnie, 2 filmy) + dwa krótkie zatwierdzenia z telefonu.
Szacunek docelowy: **~1–1,5 h tygodniowo**.

Czego **nie da się** (dziś) zautomatyzować w 100% — i dlaczego:
| Element | Przyczyna | Rozwiązanie |
|---|---|---|
| Publikacja publiczna przez API | Filmy wgrane przez API z niezweryfikowanego projektu Google Cloud (utworzonego po 28.07.2020) są **blokowane jako prywatne** do czasu audytu API | Wniosek o audyt na starcie; do tego czasu: wgranie prywatne → 1 klik „Publiczny/Zaplanuj” w Studio |
| Plansza końcowa, karty, przypięty komentarz, Test & Compare | Brak w YouTube Data API | ~5 min w YouTube Studio na film (lista kontrolna z agenta) |
| Zatwierdzenie treści | Kanał finansowy: ryzyko wycieku parametrów strategii, błędnej liczby, braku disclaimera | **Dwie bramki z telefonu** (scenariusz, podgląd prywatny) — świadomie zostawione |

## Decyzje (2026-10-29)
- **Bramki:** 2 — akceptacja scenariusza i podglądu prywatnego filmu.
- **Render: worker on-demand w Hetznerze** (decyzja 2026-10-29; zastępuje wcześniejszy plan „render na
  `claudecore` z `MemoryMax`”). `claudecore` zostaje **orkiestratorem** (maszyna stanów, bot Discord,
  `inbox/` Syncthing), a transkrypcja i render idą na **jednorazową maszynę** stawianą z API i kasowaną po
  zadaniu. Powód: na `claudecore` działa kilkanaście sesji Claude Code (~300 MB każda, ~5 z 7 GB RAM) —
  ciężkie kroki mogłyby je ubić (OOM), a limity pamięci to ryzyko tylko ograniczają, zamiast je usunąć.
  Parametry maszyny i kolejność prób: **G3**.
- **Rozliczenie Hetznera: pełna rozpoczęta godzina** (bez naliczania minutowego) → nie optymalizujemy czasu
  poniżej godziny, za to **oba filmy z jednej sesji nagraniowej montujemy w jednym uruchomieniu** workera
  (jedna płatna godzina na dwa filmy). Koszt: ~0,27 € za przebieg, ~7 € rocznie.
- **Przesył:** Syncthing **po tailnecie** (decyzja 2026-11-03) — z telefonu i z komputera (OBS zapisuje do
  synchronizowanego folderu); jeden `inbox/`. Tailscale jest już na wszystkich urządzeniach, więc Syncthing
  nie potrzebuje ani jednego portu otwartego na świat. Szczegóły i instrukcja klientów: `docs/SYNC.md`.
- **Powiadomienia i akceptacje:** Discord — prywatny serwer, bot na VPS z przyciskami Akceptuj/Popraw.

## 2. Przepływ (maszyna stanów jednego filmu)
```
IDEA → SCRIPT_DRAFT → [✋ akceptacja scenariusza] → READY_TO_RECORD → RECORDED → INGESTED
→ TRANSCRIBED → ALIGNED → CUT → GRAPHICS → AUDIO_MASTERED → RENDERED → QC_PASS
→ PACKAGED → UPLOADED_PRIVATE → [✋ podgląd w aplikacji YouTube] → SCHEDULED → PUBLISHED
→ SHORTS_SCHEDULED → ANALYZED (7 i 28 dni)
```
Stan w `content/pipeline/<slug>/status.json`; przejścia wykonuje runner (timer systemd co 15 min), każdy krok
idempotentny, logowany, z powiadomieniem przy błędzie.

## 3. Elementy systemu
### A. Planowanie i treść
| # | Element | Status | Opis |
|---|---|---|---|
| A1 | Synchronizacja kontekstu z projektów | ✅ | `sync_context.py` — karty i **pliki danych** (`.csv`, `.json`, `.png`, `.jpg`, do 5 MB) z `export/yt/` fabryki do `context/factory/`; codziennie z runnera. Fabryka eksportuje już karty `funnel/` i `lessons/` (2026-11-09) |
| A2 | Kalendarz redakcyjny | ✅ | `runner.py kalendarz` → `content/calendar.md`: terminy z `config/kanal.json` (czwartek 17:00), rotacja filarów, embargo `publish_after`, bufor 2 filmów z ostrzeżeniem co tydzień |
| A3 | Wybór tematu | ✅ | runner co tydzień uruchamia `/pomysly` (G6) i wysyła plik pomysłów; wybór: `runner.py nowy <slug> --zrodlo …` |
| A4 | Scenariusz EN+PL z ID zdań | ✅ | agent `yt-scriptwriter`, `/scenariusz` |
| A5 | Biblioteka haków | ✅ | `scripts/hooks_library.py --dane <raport yt_research>` → `docs/research/hooks.md` (pierwsze 20 s outlierów przez `yt_watch.py`); czyta ją `yt-scriptwriter`. Uruchamiać przy kwartalnym researchu |
| A6 | Kontrola zgodności | ✅ | `scripts/compliance.py` — scenariusz i pakiet: zakazane słowa w tytule, kwoty, język sprzedaży o sobie, embargo, zastrzeżenie, CTA nie przed 30 s, belka raz na film, brak PL, liczby wskazane do sprawdzenia z kartą. Kod 1 przy błędach; uruchamia ją `yt-scriptwriter`. Nie zastępuje bramki właściciela: nie oceni, czy opis zdradza logikę strategii |

### B. Nagranie (Twoja część) i przesył
| # | Element | Status | Opis |
|---|---|---|---|
| B1 | Teleprompter | ✅ | `<slug>.teleprompter.txt` → darmowa aplikacja na telefonie |
| B2 | Standard nagrania | ✅ | `docs/RECORDING.md` — sprzęt, kadr, światło, przebieg i nazewnictwo, z wniosków z nagrań próbnych |
| B3 | Automatyczny przesył | ✅ | **Syncthing po tailnecie** — `docs/SYNC.md`. Nasłuch tylko na adresie Tailscale, odkrywanie globalne/relaye/NAT wyłączone (zero portów na świat; `ufw` przepuszcza wyłącznie `tailscale0`). Foldery serwera `~/sync/telefon` i `~/sync/komputer` są **receive only** — nic z serwera nie wróci do telefonu. Do `inbox/` przenosi `scripts/odbierz.py` z timera co minutę: **twarde łącze** (bez drugiej kopii 200 MB; usunięcie w telefonie nie zabiera materiału z serwera) i warunek **niezmiennego rozmiaru przez 45 s** (aparat Xiaomi nie pozwala zmienić katalogu zapisu, więc synchronizujemy folder kamery, a bramką jest **nazwa pliku**: wzorce ignorowania przepuszczają wyłącznie `yt*.mp4`, a nazwę zmienia właściciel po nagraniu — materiał na kanał jest zadeklarowany, nie zgadywany z długości czy daty) — sam przesył Syncthinga jest atomowy, ale OBS pisze prosto do folderu synchronizowanego, więc serwer widzi rosnący plik pod docelową nazwą. Osobne `~/sync` zamiast synchronizowania `inbox/` wprost: inaczej każda operacja montażu byłaby dla Syncthinga lokalną zmianą do pogodzenia |
| B4 | Sesje seriami | ✅ | runner zbiera wszystkie nagrane filmy i montuje je jednym `worker.py job --film … --film …` (jedna opłacona godzina); przy niskim buforze podaje listę scenariuszy na sesję |

### C. Postprodukcja (worker on-demand — patrz G3)
| # | Element | Status | Opis |
|---|---|---|---|
| C0 | Nagranie próbne do testów | ✅ | `scripts/nagranie_probne.py` — mowa z `espeak-ng` + `testsrc2`, 8 zdań ze scenariuszem `content/scripts/_test-pipeline.md`, w tym **zdanie powtórzone po pomyłce** i urwane ujęcie. Test jest powtarzalny i nie zużywa czasu właściciela; prawdziwe nagranie i tak brzmi za każdym razem inaczej, więc do regresji by się nie nadawało |
| C1 | Ingest | ✅ | `scripts/ingest.py` — ffprobe (wymiary **po obrocie**: telefon zapisuje kadr poziomo i dokłada metadane obrotu, więc nagranie pionowe raportuje się jako 1920×1080; pionowe = głośne ostrzeżenie), `audio.wav` 16 kHz mono, pomiar EBU R128, `--normalize` do 1080p/30 CFR (kosztowne, domyślnie wyłączone — lokalnie niepotrzebne, robi to worker) |
| C2 | Transkrypcja słowo po słowie | ✅ | `scripts/transcribe.py` — faster-whisper (CPU, int8), venv `~/.venvs/whisper`; wagi modelu w snapshocie workera. Lokalnie `tiny`/`base`, produkcyjnie `large-v3` |
| C2a | Dwie pułapki rozwiązane w kodzie | ✅ | **(1)** Whisper na całym pliku potrafi milcząco pominąć początek — test 2026-11-02: z 36 s zjadał pierwsze 7,7 s (czyli hook), a ten sam fragment osobno transkrybował poprawnie. Dlatego nagranie idzie do modelu **kawałkami ciętymi po ciszy (VAD)**, z przesunięciem czasów; przy okazji granice ciszy pokrywają się z granicami ujęć. **(2)** Własne wczytywanie WAV zamiast ścieżki — dekoder faster-whisper idzie przez PyAV, a `av` 19 wywraca się na zmienionym API |
| C3 | Dopasowanie do scenariusza | ✅ | `scripts/align.py` — kandydaci na ujęcia (fuzzy, kotwice na pierwszym słowie), wybór jednego ujęcia na zdanie przez programowanie dynamiczne z zachowaniem kolejności, przy remisie **ujęcie późniejsze** (sprawdzone na prawdziwym głosie 2026-11-02: z trzech ujęć L012 wybrane trzecie). Okno kandydata **przycinane do faktycznie pasujących słów** — zgrubne okno zagarniało początek następnego zdania, przez co dwa sąsiednie ujęcia „nachodziły” na siebie i jedno wypadało z montażu (tak przepadły L002 i L006 w pierwszym przebiegu); `align.json` + `align-raport.md` („co wycięto”, „zdania bez ujęcia do dogrania”). Whisper potrafi schować urwany początek, rozciągając słowa na przerwę (test 2026-11-03: L005) — gdy po długim słowie ostatni fragment mowy mieści całe zdanie, a według transkrypcji padło w nim tylko kilka słów, ujęcie jest przycinane; podobne przypadki bez tych cech idą do sekcji „Do odsłuchu” raportu |
| C4 | Lista cięć + oś czasu | ✅ | `scripts/cut.py` — oś czasu, EDL CMX3600 dla DaVinci, montaż zgrubny (`--draft`). Render **odcinek po odcinku + demukser `concat`**: jeden graf filtrów z gałęzią `trim` na sklejkę wyczerpał pamięć serwera (OOM 2026-11-02) i nie skalowałby się na ~100 zdań. Obraz bierze z `video.mp4` z C1 (znormalizowany), nie z oryginału: czasy cięć pochodzą z dźwięku, a przy zmiennej liczbie klatek z kamery cięcie na oryginale rozjeżdża się z dźwiękiem. Sprawdzone end-to-end 2026-11-02. Oś czasu w `cut.json` powstaje z długości wyrenderowanych odcinków, bo każdy wychodzi nieco dłuższy od planu (0,45 s na 12 odcinkach) |
| C5 | Dźwięk | ✅ | `scripts/audio_master.py` — highpass 80 Hz, `afftdn`, kompresor, **podbicie wejścia do poziomu roboczego** (bez tego cichy materiał w ogóle nie dochodzi do progu kompresora — nagranie telefonem miało −30 LUFS), potem pomiar `loudnorm` → `volume` → `alimiter` z nawrotami na poziom **i na szczyt** (koder AAC przestrzeliwuje limiter o ~1,3 dB) do −14 LUFS / −1,5 dBTP, `--music` z duckingiem (`sidechaincompress`), raport przed/po z listą uwag. Samo `loudnorm:linear=true` nie dochodzi do celu (przycina podbicie przy szczycie) i potrafi zostawić szczyt **ponad** limitem — test 2026-11-02 dał −16,7 LUFS przy −0,97 dBTP. Teraz szczyt trzyma limit; na prawdziwym nagraniu wychodzi −14,3 LUFS przy −1,63 dBTP, na syntetycznym −14,5 przy −1,87 |
| C6 | Obraz | ✅ | Korekcja `scripts/grade.py` (LUT, podgląd przed/po, render po wyborze `--kolor`). Najazd `TWARZ: AKCENT` w scenariuszu → `align.py` oznacza zdanie, `cut.py` robi powolny najazd 1,0→1,08 (zoompan na obrazie 2×, bez drżenia). Naprzemienne przybliżenie na sklejkach w C4 |
| C7 | Ekrany i grafiki | ✅ | `scripts/graphics.py` — plan zdjęciowy z kolumny „Na ekranie” (sąsiednie zdania z tym samym poleceniem = jeden plan, czasy z `cut.json`), szablony Pillow (`equity`, `lejek`, `metryki`, `cytat`, `diagram`, `lista`; dwa ostatnie bez liczb) w palecie miniatur, nałożenie jednym przejściem FFmpeg z przenikaniem 0,35 s. **Liczby wyłącznie z pliku `--dane`** — brak danych to błąd, nie zachęta do wymyślenia wykresu; `zrodlo: "test"` wypala znak wodny DANE TESTOWE. Rozmiar grafiki brany z kadru filmu, nie na sztywno. To właściwe lekarstwo na widoczne sklejki (C4 ma tylko protezę). `BELKA: subscribe` w scenariuszu: mała belka z nazwą kanału i przyciskiem przy CTA głosem, raz na film, 4 s, bez `--dane`; logo dojdzie po F6 |
| C8 | Napisy | ✅ | `scripts/subtitles.py` — SRT EN (tekst ze scenariusza, czasy z nagrania) + SRT PL. Tekst ze scenariusza, nie z transkrypcji: Whisper słyszy „10 minutes” tam, gdzie w scenariuszu jest „ten minutes”, i nie zna pisowni nazw własnych. Słowa scenariusza przypinane do usłyszanych (`SequenceMatcher`), brakującym czas interpolowany; czasy w **osi montażu**, nie nagrania. PL dzielone na tyle samo kawałków co EN i dostaje te same czasy. Łamanie do 2 linii po 42 znaki |
| C9 | Rozdziały | ✅ | `scripts/chapters.py` — timestampy z `cut.json`, nie z planu w scenariuszu (po cięciu film ma inną długość). Sprawdza trzy warunki YouTube'a: pierwszy rozdział `0:00`, min. 3 rozdziały, każdy min. 10 s — i mówi, który nie wyszedł |
| C10 | Intro/outro i plansza końcowa | ✅ | `scripts/finish.py`: plansza końcowa 10 s (5–20) i opcjonalne `--intro` (3 s, logo + dźwięk identyfikacji `assets/brand/ident.wav`); napisy i rozdziały przesuwane o intro, od kopii, więc powtórka jest bezpieczna |
| C11 | Render | ✅ | `scripts/finish.py` — `final.mp4` z najdalszego etapu montażu, bez ponownego kodowania filmu (demukser `concat`), `+faststart`. Styk z planszą sprawdzony na serwerze 2026-11-03; na workerze jeszcze nie uruchomione |
| C12 | QC automatyczne | ✅ | `scripts/qc.py` — format, sync A/V, błędy dekodowania, czarne klatki, cisza, EBU R128, zgodność z osią czasu, napisy, rozdziały, długość; `qc.json` + `qc-klatki.jpg` do obejrzenia. Wykrywanie sprawdzone na plikach z celowymi usterkami. Domyślnie kod 0, żeby worker zdążył zabrać wyniki; `--strict` daje 1 przy FAIL |
| C13 | Shorts | ✅ | `scripts/shorts.py` na `claudecore` po pakiecie: zakresy ID z `content/publish/<slug>/shorts.json`, wycinek 9:16 z montażu bez grafik, napisy ASS słowo po słowie (Anton, aktywne słowo zielone), limit 59 s; wgrywa `upload.py short` z linkiem do filmu |

### D. Opakowanie i publikacja
| # | Element | Status | Opis |
|---|---|---|---|
| D1 | Pakiet publikacji | ✅ | agent `yt-producer`, `/publikacja` (tytuły, opis, tagi, miniatury, shorts, checklista) |
| D2 | Miniatury | ✅ | `thumbnail.py --szablon A|B|C`: trzy stałe szablony serii (A werdykt: karta + twarz, B liczba z karty, C pytanie z dużą twarzą), te trzy idą do Test & Compare; `yt-producer` generuje je na `claudecore` (wystarczy Pillow). Kontrola `thumbnail_check.py` i sceny HTML mają zależności w snapshocie workera (G3c). Zdjęcia twarzy do `assets/face/` dostarcza właściciel |
| D3 | Upload przez API | ✅ | `scripts/upload.py` (`film`, `zaplanuj`, `short`, `playlisty`, `--na-sucho`): wznawialne wysyłanie, miniatura, napisy EN/PL, lokalizacja PL, playlista filaru, Education, EN. Metadane z `metadata.json` pakietu. **Czeka na klienta OAuth i `yt_api.py autoryzuj`**; sprawdzone na sucho |
| D4 | Audyt API YouTube | 🟡 | szkic polityki i lista do wniosku: `docs/legal/privacy-youtube-api.md`. Złożenie wniosku i publikacja polityki — właściciel (wymaga decyzji o stronie). Do tego czasu filmy przez API są prywatne, termin ustawiasz w Studio (runner o tym przypomina) |
| D5 | Lista ręczna w Studio | ✅ | po wgraniu runner wysyła `checklist.md` z pakietu z linkiem do edycji w Studio |

### E. Po publikacji
| # | Element | Status | Opis |
|---|---|---|---|
| E1 | Analityka | ✅ | `scripts/analytics.py raport` po 7 i 28 dniach (runner): metryki, źródła ruchu, **spadki utrzymania przypięte do ID zdań** z `cut.json`; CTR i Test & Compare przepisujesz ze Studia (brak w API) |
| E2 | Komentarze | ✅ | `scripts/komentarze.py` codziennie: nowe komentarze → `content/comments/<data>.md` z propozycjami odpowiedzi agenta; wysyłka tylko ręcznie `komentarze.py odpowiedz <ID> "…"` |
| E3 | Newsletter | ✅ | `scripts/newsletter.py` co miesiąc: szkic `content/newsletter/RRRR-MM.md` z karty `funnel/` i filmów miesiąca; wysyłka po Twojej stronie |
| E4 | Research kwartalny | ✅ | `yt_research.py` / `yt_watch.py` |

### F. Fundament kanału (jednorazowo)
| # | Element | Status | Opis |
|---|---|---|---|
| F1 | Konto | ⬜ | **właściciel**: konto marki, `@radoslawlubas`, weryfikacja telefonu |
| F2 | Wygląd | ✅ | `scripts/brand.py` → `assets/brand/`: awatar, baner, znak wodny (wersje wybrane 2026-11-05). Wgranie w Studio — właściciel |
| F3 | Opisy | 🟡 | `docs/CHANNEL_SETUP.md`: opis EN + PL z linkiem do profilu mql5.com. **Brakuje e-maila kontaktowego** |
| F4 | Domyślne ustawienia przesyłania | ✅ | wartości w `docs/CHANNEL_SETUP.md`; `upload.py` i tak ustawia je przy każdym filmie |
| F5 | Układ kanału | 🟡 | playlisty filarów tworzy `upload.py playlisty` (nazwy w `config/kanal.json`); sekcje strony kanału ustawiasz w Studio |
| F6 | Brand kit | ✅ | `assets/brand/`: logo (awatar, znak wodny), dźwięk identyfikacji `ident.wav`, belka subskrypcji i belka z imieniem (`BELKA: imie`) z logo, plansza końcowa, intro |
| F7 | Strona i prawo | ⬜ | **właściciel** (osobny projekt): zdjąć przykładowe liczby, Methodology, Ledger, polityka z `docs/legal/` |

### G. Infrastruktura
| # | Element | Status | Opis |
|---|---|---|---|
| G0 | Limit pamięci na claudecore | ✅ | `scripts/proc.py` — ciężkie kroki przez `systemd-run -p MemoryMax -p MemorySwapMax=0`, żeby OOM ubił nasz proces, a nie sesje Claude Code (lekcja 2026-11-02). Na workerze `--mem-max 0`. |
| G1 | Runner + stan | ✅ | `scripts/runner.py`: `content/pipeline/<slug>/status.json`, 15 stanów, kroki idempotentne, 3 próby z powiadomieniem, blokada przed równoległym przebiegiem, zadania okresowe (kontekst, retencja, komentarze, pomysły, bufor, newsletter), commit zmian w `content/`. Timer: `docs/OPERACJE.md` |
| G2 | Powiadomienia i akceptacje | ✅ | `scripts/discord.py`: wiadomości z załącznikami, bramki przez reakcje ✅/🔁 i uwagi w odpowiedzi (bez stałego procesu). **Czeka na bota i `~/.config/yt_channel/discord.json`**; do tego czasu log `content/pipeline/_powiadomienia.log` i `runner.py akceptuj/popraw` |
| G3 | Worker on-demand (Hetzner) | ✅ | `scripts/worker.py` (`up`/`down`/`job`/`reap`). Pierwszy pełny przebieg 2026-11-02: CCX33 @ hel1, C1–C5 na nagraniu próbnym, maszyna skasowana automatycznie; cloud-init + `large-v3` = ~6 min narzutu na instalację, stąd snapshot (G3b). Token: `~/.config/yt_channel/hetzner_api_token` (600), klucz SSH `~/.ssh/yt_worker` wgrywany do projektu przez API przy pierwszym `up`. | **CCX33** — 8 dedykowanych vCPU AMD, 32 GB RAM, 240 GB NVMe, €0,273/h (General Purpose: brak „limited availability”). **Ubuntu 24.04 LTS** (ta sama wersja co `claudecore` — debugujemy lokalnie, uruchamiamy zdalnie). Start ze **snapshotu** (FFmpeg + venv `faster-whisper` + wagi modelu), x86 → ten sam obraz działa na wszystkich wariantach fallbacku. Dane przez `rsync` po SSH, **bez volume** (volume podpina się tylko do jednej maszyny naraz i jest przywiązany do lokalizacji). Dostęp: wyłącznie klucz SSH, firewall inbound = SSH tylko z IP `claudecore` |
| G3a | Kolejność prób (fallback) | ✅ | W kodzie (`LANCUCH`): `ccx33 hel1 → ccx33 fsn1 → ccx33 nbg1 → cpx42 hel1 → cx43 hel1`. **hel1 pierwszy, bo `claudecore` stoi w Helsinkach** (konsola Hetznera, 2026-11-02) — worker ląduje w tym samym DC co dane. | Typ ważniejszy niż lokalizacja (opóźnienie między DC nie ma znaczenia dla `rsync`, przewidywalność rdzeni ma): `CCX33 fsn1` → `CCX33 hel1` → `CCX33 nbg1` → `CPX42 fsn1` → `CX43 fsn1`. Dwa ostatnie to współdzielone vCPU: wolniej i taniej, ale produkcja nie staje. Lokalizacje spoza eu-central pomijamy (dopłata, odległość) |
| G3b | Cykl życia snapshotu | ✅ | `worker.py snapshot build|list|promote|prune`: budowa skryptem na najmniejszej maszynie (obraz pasuje do całego łańcucha), wersje pip przypięte w `config/requirements-*.txt` po pierwszej budowie, nowy obraz jako `kandydat`, test `job --obraz kandydat`, potem `promote`; zostaje produkcyjny i jeden poprzedni. Pierwszy obraz zbudowany 2026-11-09 (6,1 GB, cx23 @ hel1), przetestowany na dwóch filmach w jednym przebiegu i promowany do produkcji |
| G3c | Zawartość snapshotu | ✅ | FFmpeg, Tesseract, fonty, venv `whisper` (faster-whisper + wagi `large-v3`), venv `narzedzia` (Pillow, OpenCV, pytesseract, Playwright + Chromium, rembg + `u2net_human_seg`); wersje w `config/wersje-systemu-workera.txt` |
| G7 | Watchdog kosztów | ✅ | `worker.py reap --older-than 0.967` co minutę: `~/.config/systemd/user/worker-reap.{service,timer}`, skrypt z głównego katalogu projektu. Maszynę starszą niż **58 min** kasuje przed naliczeniem kolejnej godziny, także tę zostawioną do diagnozy po błędzie. Trwającego `job` nie rusza (`~/.local/state/yt_channel/worker-job.pid`), chyba że minęły 3 h |
| G8 | Logi workera | ✅ | po każdym kroku `rsync` lekkich plików (log, JSON, SRT, raporty, podglądy) na `claudecore`, więc przy awarii logi zostają |
| G4 | Magazyn i retencja | ✅ | `scripts/retencja.py` codziennie: 30 dni po publikacji usuwa surowe nagranie (inbox + kopia Syncthinga) i etapy pośrednie, zostawia `final.mp4`, shorts i raporty; ostrzeżenie przy dysku > 80% |
| G5 | Sekrety | ✅ | wszystko w `~/.config/yt_channel/` (600): Hetzner, Gemini, klucz API YouTube, OAuth (`youtube_oauth_client.json`, `youtube_token.json`), Discord (`discord.json`); żaden skrypt ich nie wypisuje |
| G6 | Uruchamianie agentów bez czatu | ✅ | `scripts/agent.py`: `claude -p` z wąską listą narzędzi (pliki, `compliance.py`, `thumbnail.py`), log w `content/pipeline/_agenci/`; runner używa go do scenariuszy, poprawek, pakietów, pomysłów, komentarzy i newslettera |

## 4. Kolejność budowy
| Etap | Zakres | Efekt |
|---|---|---|
| **0. Fundament** | F1–F7, D4 (wniosek o audyt), B2, B3 | kanał gotowy wizualnie i prawnie; nagrania same trafiają na serwer |
| **1. MVP „nagranie → prywatny film”** | C1–C5, C8–C12, D3, G1, G3, G7, G8 — **C1–C3 gotowe (2026-11-02)**, dalej C4 (lista cięć) i C5 (dźwięk) | z jednego nagrania: zmontowany film 1080p z napisami EN/PL, rozdziałami, pakietem i wgraniem prywatnym |
| **2. Grafiki i shorts** | C6, C7, C13, A1 (dane) | ekrany i wykresy z danych fabryki, shorts automatycznie |
| **3. Orkiestracja** | A2, A3, G2, G6, B4 | kalendarz, bufor, akceptacje z telefonu, praca seriami |
| **4. Pętla wzrostu** | E1–E3, A5 | analityka → reguły, komentarze, newsletter, biblioteka haków |
| **5. Opcjonalnie** | miniatury AI (opcja 2), 4K, zaawansowany motion design | po 5–10 filmach, na danych z testów A/B |

## 5. Ryzyka
- ~~**Pamięć VPS** (sesje Claude Code)~~ → **rozwiązane** przeniesieniem ciężkich kroków na workera on-demand (G3);
  na `claudecore` zostaje sama orkiestracja.
- **Niedostępność typu lub lokalizacji** przy stawianiu maszyny z API (`resource_unavailable`) → łańcuch fallbacku G3a.
- **Wyciek kosztów** — worker nieusunięty po błędzie nalicza kolejne godziny → watchdog G7 (niezależny od pipeline'u).
- **Utrata logów** razem ze skasowaną maszyną → G8 (logi wypychane na bieżąco).
- **Audyt API** może potrwać tygodnie → do tego czasu publikacja jednym kliknięciem.
- **Jakość dźwięku** to największa dźwignia jakości przy 0 zł → standard nagrania, potem ewentualnie mikrofon krawatowy.
- **Koszt tokenów** przy grafikach → szablony wielokrotnego użytku zamiast generowania od zera.
- **Błąd merytoryczny / wyciek** → kontrola zgodności + bramka scenariusza + podgląd prywatny.

## Źródła (fakty techniczne)
- Blokada prywatna dla niezweryfikowanych projektów API: https://developers.google.com/youtube/v3/docs/videos/insert
- Plansze końcowe i karty edytowane w YouTube Studio: https://support.google.com/youtube/answer/6388789
