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
- **Render:** VPS `claudecore` (fabryka EA działa na innych serwerach). Bez limitów CPU; **tylko limit pamięci
  i niski priorytet** (`MemoryMax`, `nice`/`ionice`) — na serwerze działa kilkanaście sesji Claude Code
  (~300 MB każda, ~5 z 7 GB RAM zajęte), a transkrypcja + render bez limitu mogłyby je ubić (OOM).
- **Przesył:** Syncthing — z telefonu i z komputera (OBS zapisuje do synchronizowanego folderu); jeden `inbox/`.
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
| A1 | Synchronizacja kontekstu z projektów | 🟡 | `sync_context.py` (+ tryb `export_dir`); fabryka musi zacząć eksportować karty; **rozszerzyć o pliki danych** (`equity.csv`, `report.png`) do grafik |
| A2 | Kalendarz redakcyjny | ⬜ | `content/calendar.md`: rotacja filarów, 1 film/tydz., **bufor 2 gotowych filmów**, daty embarg |
| A3 | Wybór tematu | 🟡 | `/pomysly` → automatycznie co tydzień, wynik do kalendarza |
| A4 | Scenariusz EN+PL z ID zdań | ✅ | agent `yt-scriptwriter`, `/scenariusz` |
| A5 | Biblioteka haków | ⬜ | haki z filmów-outlierów niszy (`yt_research.py` + `yt_watch.py`) → `research/hooks.md` |
| A6 | Kontrola zgodności | 🟡 | zakazane słowa, język sprzedaży, liczby vs karta, embargo, disclaimer — jako skrypt + bramka |

### B. Nagranie (Twoja część) i przesył
| # | Element | Status | Opis |
|---|---|---|---|
| B1 | Teleprompter | ✅ | `<slug>.teleprompter.txt` → darmowa aplikacja na telefonie |
| B2 | Standard nagrania | ⬜ | `docs/RECORDING.md`: kadr, światło, dźwięk, 1080p/30 lub 4K/30, „pomyłka → powtórz całe zdanie”, nazewnictwo |
| B3 | Automatyczny przesył | ⬜ | **Syncthing** (darmowy, bez chmury): telefon i komputer (OBS) → VPS `inbox/`; runner wykrywa nowe pliki |
| B4 | Sesje seriami | ⬜ | 2 scenariusze na sesję co 2 tygodnie |

### C. Postprodukcja (VPS, lekko, z limitami zasobów)
| # | Element | Status | Opis |
|---|---|---|---|
| C1 | Ingest | ⬜ | ffprobe, kopia, normalizacja do 1080p/30 CFR, wyciągnięcie audio |
| C2 | Transkrypcja słowo po słowie | ⬜ | faster-whisper (CPU, int8), lokalnie |
| C3 | Dopasowanie do scenariusza | ⬜ | słowa ↔ ID zdań (fuzzy), **ostatnie czyste ujęcie** każdego zdania, wycięcie pauz/powtórek; raport „co wycięto” |
| C4 | Lista cięć + oś czasu | ⬜ | EDL/FCPXML dla DaVinci (ręczna poprawka opcjonalna) + render automatyczny FFmpeg |
| C5 | Dźwięk | ⬜ | filtr górnoprzepustowy, odszumianie, kompresja, **loudnorm −14 LUFS**, muzyka pod głosem z duckingiem |
| C6 | Obraz | ⬜ | korekcja/LUT, subtelne przybliżenia na akcentach (z beat mapy), bez efekciarstwa |
| C7 | Ekrany i grafiki | ⬜ | szablony kodem: equity IS/OOS, lejek, stres spreadu (z danych karty), zrzuty publikacji (PDF → obraz), nagrania terminala (VHS); **szablony wielokrotnego użytku**, nie generowane od zera (koszt tokenów) |
| C8 | Napisy | ⬜ | SRT EN (tekst ze scenariusza, czasy z nagrania) + SRT PL (kolumna PL) |
| C9 | Rozdziały | ⬜ | timestampy sekcji z rzeczywistego montażu → opis |
| C10 | Intro/outro i plansza końcowa | ⬜ | 3 s identyfikacji marki + 20 s tła pod planszę końcową |
| C11 | Render | ⬜ | 1080p H.264 (YouTube rekomendacje), w oknie bez obciążenia fabryki, `CPUQuota`/`MemoryMax`, szkic w ½ rozdzielczości |
| C12 | QC automatyczne | ⬜ | rozdzielczość, sync A/V, czarne klatki, cisza, głośność (EBU R128), długość, rozmiar; Claude ogląda klatki co N s (grafika na twarzy, mignięcia) |
| C13 | Shorts | ⬜ | 3–5 × 9:16 z zakresów ID, napisy wypalone słowo po słowie, link do filmu |

### D. Opakowanie i publikacja
| # | Element | Status | Opis |
|---|---|---|---|
| D1 | Pakiet publikacji | ✅ | agent `yt-producer`, `/publikacja` (tytuły, opis, tagi, miniatury, shorts, checklista) |
| D2 | Miniatury | ✅ | `thumbnail.py` (simple/rich), siatka, face lock |
| D3 | Upload przez API | ⬜ | OAuth (nie klucz API), `videos.insert` prywatnie, miniatura, napisy EN/PL, **lokalizacje tytułu i opisu PL**, playlista filaru, kategoria Education, język EN |
| D4 | Audyt API YouTube | ⬜ | wniosek na starcie (wymaga polityki prywatności na quantinvest.co) → potem planowanie publikacji przez API |
| D5 | Lista ręczna w Studio | 🟡 | plansza końcowa, karty, przypięcie komentarza, Test & Compare — generowana przez agenta |

### E. Po publikacji
| # | Element | Status | Opis |
|---|---|---|---|
| E1 | Analityka | ⬜ | YouTube Analytics API (OAuth): CTR, utrzymanie widza, wyniki A/B → raport 7/28 dni → wnioski do standardu i `EDITING_RULES.md` |
| E2 | Komentarze | ⬜ | dzienny przegląd + propozycje odpowiedzi do akceptacji |
| E3 | Newsletter | ⬜ | miesięczny raport lejka z karty `funnel/` (szkic automatyczny) |
| E4 | Research kwartalny | ✅ | `yt_research.py` / `yt_watch.py` |

### F. Fundament kanału (jednorazowo)
| # | Element | Status | Opis |
|---|---|---|---|
| F1 | Konto | ⬜ | **Konto marki (Brand Account)** — możliwość dodania menedżerów, oddzielenie od prywatnego Gmaila; weryfikacja telefonu (własne miniatury, filmy >15 min) |
| F2 | Wygląd | ⬜ | awatar 800×800, baner 2560×1440 (bezpieczna strefa 1546×423), znak wodny „subskrybuj”, zwiastun kanału (film #1) |
| F3 | Opisy | ⬜ | opis kanału EN + lokalizacja PL, linki (QuantInvest, mql5.com, newsletter), e-mail kontaktowy |
| F4 | Domyślne ustawienia przesyłania | ⬜ | kategoria, język, licencja, komentarze, tagi bazowe, disclaimer w opisie |
| F5 | Układ kanału | ⬜ | sekcje i playlisty filarów |
| F6 | Brand kit | 🟡 | kolory i font są; dodać: logo/awatar, dźwięk identyfikacji, szablon dolnej belki, szablon planszy końcowej (`assets/brand/`) |
| F7 | Strona i prawo | ⬜ | quantinvest.co: Methodology, Ledger, **polityka prywatności** (audyt API), disclaimer |

### G. Infrastruktura
| # | Element | Status | Opis |
|---|---|---|---|
| G1 | Runner + stan | ⬜ | timer systemd, `status.json`, idempotentne kroki, ponawianie |
| G2 | Powiadomienia i akceptacje | ⬜ | Discord: bot na VPS (prywatny serwer, kanał #produkcja), przyciski Akceptuj/Popraw, uwagi w wątku |
| G3 | Zasoby VPS | ⬜ | ciężkie kroki przez `systemd-run -p MemoryMax=…` + `nice/ionice` (ochrona sesji Claude Code przed OOM); bez limitu CPU |
| G4 | Magazyn i retencja | ⬜ | surowe pliki usuwane 30 dni po publikacji (kopia u Ciebie/Drive), monitoring dysku |
| G5 | Sekrety | 🟡 | klucze w `~/.config/yt_channel/` (600); dodać token OAuth (odświeżany) — nigdy w repo/logach |
| G6 | Uruchamianie agentów bez czatu | ⬜ | `claude -p` (tryb nieinteraktywny) wywoływany przez runner dla scenariusza/opakowania |

## 4. Kolejność budowy
| Etap | Zakres | Efekt |
|---|---|---|
| **0. Fundament** | F1–F7, D4 (wniosek o audyt), B2, B3 | kanał gotowy wizualnie i prawnie; nagrania same trafiają na serwer |
| **1. MVP „nagranie → prywatny film”** | C1–C5, C8–C12, D3, G1, G3 | z jednego nagrania: zmontowany film 1080p z napisami EN/PL, rozdziałami, pakietem i wgraniem prywatnym |
| **2. Grafiki i shorts** | C6, C7, C13, A1 (dane) | ekrany i wykresy z danych fabryki, shorts automatycznie |
| **3. Orkiestracja** | A2, A3, G2, G6, B4 | kalendarz, bufor, akceptacje z telefonu, praca seriami |
| **4. Pętla wzrostu** | E1–E3, A5 | analityka → reguły, komentarze, newsletter, biblioteka haków |
| **5. Opcjonalnie** | miniatury AI (opcja 2), 4K, zaawansowany motion design | po 5–10 filmach, na danych z testów A/B |

## 5. Ryzyka
- **Pamięć VPS** (sesje Claude Code) → limit pamięci dla transkrypcji/renderu; przy wzroście kanału ewentualnie więcej RAM.
- **Audyt API** może potrwać tygodnie → do tego czasu publikacja jednym kliknięciem.
- **Jakość dźwięku** to największa dźwignia jakości przy 0 zł → standard nagrania, potem ewentualnie mikrofon krawatowy.
- **Koszt tokenów** przy grafikach → szablony wielokrotnego użytku zamiast generowania od zera.
- **Błąd merytoryczny / wyciek** → kontrola zgodności + bramka scenariusza + podgląd prywatny.

## Źródła (fakty techniczne)
- Blokada prywatna dla niezweryfikowanych projektów API: https://developers.google.com/youtube/v3/docs/videos/insert
- Plansze końcowe i karty edytowane w YouTube Studio: https://support.google.com/youtube/answer/6388789
