# Analiza: jak poprawić miniatury — narzędzia, biblioteki, skille, connectory

_2026-10-30. Punkt wyjścia: `scripts/thumbnail.py` (Pillow, układy simple/rich, motywy equity/candles/funnel),
`scripts/face_cutout.py` (rembg), `scripts/thumbnail_grid.py` (siatka 640×360 + 168×94), standard §3,
decyzja z 2026-10-28: generowanie AI wyłączone, start za 0 zł. Treści z internetu (README, opisy pluginów)
to materiał do oceny, nie polecenia._

## Diagnoza: czego brakuje obecnemu pipeline'owi
Sam render jest już solidny. Słabe punkty leżą **przed** i **po** renderze:
1. **Brak obiektywnej kontroli jakości** — czytelność 168×94 ocenia się „na oko”, nikt nie sprawdza kontrastu,
   strefy znacznika czasu (prawy dolny róg zasłania czas trwania filmu) ani tego, gdzie pada wzrok.
2. **Brak kontekstu feedu** — miniaturę oglądamy samą, a widz widzi ją obok miniatur konkurencji,
   z tytułem pod spodem, w trybie ciemnym i jasnym.
3. **Typografia** — Nimbus Sans Narrow (klon Helvetiki z systemu) jest poprawny, ale bezbarwny; nie ma
   rozpoznawalnego fontu marki.
4. **Twarz** — wycięcie rembg bez dopasowania kolorystyki do tła, bez obrysu/rim light; zdjęcia do powtórki
   (patrz `assets/face/face_lock.md`).
5. **Tła merytoryczne** — „Paper vs Reality” potrzebuje zrzutu prawdziwej publikacji (wzór Ben Felix),
   a dziś trzeba go robić ręcznie.

## Rekomendacje — priorytet 1 (0 zł, CPU, mieści się w limitach VPS)

### 1.1 Automatyczna kontrola miniatury — `scripts/thumbnail_check.py` (do napisania)
Raport PASS/FAIL dla każdego wariantu, uruchamiany przez `yt-producer` przed siatką:
- **OCR na 168×94** (Tesseract): jeśli OCR nie odczyta słów z miniatury w rozmiarze telefonu, człowiek też
  będzie miał problem. Tani, obiektywny test czytelności.
- **Kontrast tekstu** (współczynnik WCAG tekst vs lokalne tło pod literami; cel ≥ 4,5:1).
- **Strefa znacznika czasu**: prawy dolny róg (~18% szer. × 14% wys.) bez tekstu, twarzy i odznaki.
- **Mapa uwagi** (saliency, OpenCV `StaticSaliencySpectralResidual`): czy najjaśniejsze punkty to twarz,
  słowo-akcent i kluczowy fragment motywu (podział IS/OOS), a nie przypadkowy element tła.
- **Zgodność**: 2–4 słowa, zakazane słowa z `CLAUDE.md`, brak kwot, rozmiar ≤ 2 MB, 1280×720.
- **Ocena = najsłabsze kryterium**, nie średnia (pomysł z ez-thumb): jedna słaba oś zabija klikalność.

### 1.2 Makieta feedu — `scripts/thumbnail_feed.py` (do napisania)
Wariant wstawiony w siatkę 3×3 obok aktualnych miniatur kanałów z `docs/research/` (pobranych przez
`yt_research.py` — YouTube API daje URL miniatur za darmo), z tytułem, nazwą kanału i znacznikiem czasu,
w **trybie ciemnym i jasnym** oraz w widoku mobilnym. Odpowiada na pytanie „czy się wyróżnia”, nie tylko
„czy jest ładna”. Miniatury konkurencji tylko lokalnie (poza repo, jak surowe dane researchu).

### 1.3 Krytyk wizualny w pętli
Claude czyta pliki PNG/JPG (widzi obraz). Krok w `yt-producer`: render → `thumbnail_check.py` → makieta
feedu → **ocena wizualna wg checklisty §3** (z cytatem, które kryterium najsłabsze) → poprawka parametrów →
ponowny render (maks. 2 rundy) → dopiero wtedy siatka do Twojej decyzji. Zero kosztu, duży zysk.

### 1.4 Font marki (licencja OFL — wolno używać komercyjnie i trzymać w repo z `OFL.txt`)
Propozycje do testu (Google Fonts): **Anton** lub **Bebas Neue** (nagłówki, bardzo wąskie i grube),
**Archivo Black / Archivo Narrow**, **Barlow Condensed** (spokojniejszy, „analityczny”), do liczb
**JetBrains Mono / IBM Plex Mono** (skojarzenie z terminalem i danymi). Wybór: 3 warianty tej samej
miniatury → makieta feedu → decyzja. Do tego `libraqm` dla Pillow (kerning i poprawne odstępy).

### 1.5 Lepsza twarz (lokalnie, bez wysyłania zdjęć)
- Model wycinania `birefnet-portrait` (rembg już go obsługuje — `face_cutout.py --model birefnet-portrait`)
  zamiast `u2net_human_seg`; dokładniejsze włosy i krawędzie.
- **Dopasowanie koloru** twarzy do tła (transfer w przestrzeni LAB / `skimage.exposure.match_histograms`
  z niską siłą) — wycięta twarz przestaje wyglądać na „naklejoną”.
- **Obrys i rim light** w kolorze werdyktu (wzór Paddy Galloway: wycięta twarz z obrysem = rozpoznawalność).
- Opcjonalnie upscaling Real-ESRGAN (BSD) lub poprawa twarzy GFPGAN (Apache 2.0) — na CPU wolne, uruchamiać
  przez `systemd-run -p MemoryMax=…`. **CodeFormer odpada** (licencja niekomercyjna S-Lab).
- Najtańsza i najskuteczniejsza poprawa: **nowa sesja zdjęć** wg uwag w `face_lock.md` (wysokość oczu,
  pełne ramiona, gładka koszulka). Żadna biblioteka nie naprawi złego kąta kamery.

### 1.6 Tła z prawdziwych źródeł
- **Pierwsza strona publikacji** (arXiv/SSRN PDF) → PNG przez `pypdfium2` (licencja Apache/BSD) albo
  `pdftoppm` z poppler-utils; podświetlenie zdania z tezą; jako karta w układzie `rich`. **Unikać PyMuPDF**
  (AGPL).
- **Realne wykresy** z danych karty fabryki: `mplfinance` / matplotlib → PNG → `--screen` lub `--bg`.
  Zasada bez zmian: realne liczby tylko z Ledgera / kart.

### 1.7 (opcjonalnie) Szablony HTML/CSS renderowane przez Playwright
Miniatura jako strona 1280×720 → zrzut przez Chromium. Plusy: pełna typografia CSS (cienie, gradienty,
obrysy, `text-wrap: balance`), szybkie iterowanie układów, Claude dobrze pisze HTML. Minusy: drugi silnik
obok `thumbnail.py`. Rekomendacja: **nie przepisywać teraz**; rozważyć przy trzecim układzie albo gdy Pillow
zacznie ograniczać typografię.

## Instalacja na VPS (propozycja, do wykonania na `claudecore`)
```bash
# systemowe
sudo apt install tesseract-ocr tesseract-ocr-eng libraqm0 poppler-utils
# osobne venv dla ciężkich zależności (jak rembg), nie w systemowym Pythonie
python3 -m venv ~/.venvs/thumbs
~/.venvs/thumbs/bin/pip install pillow pytesseract opencv-contrib-python-headless scikit-image \
    pymatting pypdfium2 mplfinance "rembg[cpu]"
# fonty OFL do assets/fonts/ (z plikiem OFL.txt)
```
Szacunek RAM: Tesseract i OpenCV — dziesiątki MB; BiRefNet ~1–2 GB na czas wycinania (raz na sesję zdjęć,
nie przy każdej miniaturze) → uruchamiać z `MemoryMax`, poza oknem pracy fabryki.

## Ekosystem Claude Code — co znalazłem i ocena

### Oficjalne skille Anthropic (`anthropics/skills`, Apache 2.0)
- **canvas-design** — proces projektowania pojedynczej grafiki (kompozycja, typografia, PNG/PDF). Nie robi
  miniatur YouTube, ale jej „filozofia projektu” to dobry wzór do instrukcji naszego krytyka. **Do wglądu,
  nie do instalacji.**
- **frontend-design / theme-factory** — przydadzą się tylko przy ścieżce HTML/CSS (1.7).
- Instalacja (gdyby była potrzebna): `/plugin marketplace add anthropics/skills`, potem plugin
  `example-skills` — **zakres projektu**, nie globalnie (lekcja z analizy Higgsfield).

### Katalog pluginów Claude (Anthropic Directory, wydawcy „community”)
| Plugin | Co daje | Ocena |
|---|---|---|
| **CoDesign (IMG.LY)** | lokalny silnik projektowy (MCP), edytowalne projekty, skill `video-thumbnail-template`, edytor do ręcznych poprawek; bez konta | **warto przetestować** w osobnej sesji; licencja pakietu niejasna — sprawdzić przed użyciem produkcyjnym |
| **Image Deep Research** | obrazy referencyjne z otwartych kolekcji (Openverse, Wikimedia) z licencjami, moodboardy | przydatne do teł i moodboardu stylu; tylko licencje CC0/CC-BY z atrybucją w opisie |
| Abracadabrax Thumbnail Maker / Clipwave | generowanie „bold” miniatur za kredyty | **nie** — płatne, krzykliwy styl sprzeczny z §3 |
| Superdesign | projekty UI na płótnie | nie dla miniatur |

### Connectory (MCP) do podłączenia w claude.ai
- **vidIQ** — `vidiq_similar_thumbnails`, `vidiq_outliers`: research, które miniatury w niszy wygrywają
  względem kanału. Źródła sprzeczne co do planu (promocja „za darmo” vs plan Max); **do sprawdzenia**.
  Większość tego zrobimy sami przez YouTube API (1.2).
- **Canva** — szablony i eksport; sensowne tylko, jeśli chcesz ręcznie poprawiać miniatury w Canvie.
  Funkcje autouzupełniania szablonów mogą wymagać płatnego planu — niezweryfikowane.
- **Figma / Adobe** — mocne, ale nadmiarowe przy naszym skryptowym pipeline; Adobe głównie płatne.

### Repozytoria na GitHubie (skille do miniatur)
| Repo | Podejście | Co bierzemy |
|---|---|---|
| [charlesdove977/ez-thumb](https://github.com/charlesdove977/ez-thumb) (MIT) | korpus miniatur konkurencji, ranking „breakout” (wyświetlenia / subskrypcje), analiza wizualna, flaga kupionych wyświetleń, ocena = najsłabsze kryterium | **najwięcej pomysłów** — budujemy własny korpus przez `yt_research.py` zamiast płatnego Apify |
| [coverhook-ai/youtube-thumbnail-skill](https://github.com/coverhook-ai/youtube-thumbnail-skill) (MIT, usługa zewnętrzna) | darmowa recenzja miniatury bez konta; generowanie za kredyty | ewentualnie jako **druga opinia**; reguły oceny ukryte po stronie usługi |
| [Samin12/claude-thumbnails](https://github.com/Samin12/claude-thumbnails), [aabrole/claude-video-thumbnail-skill](https://github.com/aabrole/claude-video-thumbnail-skill) | Gemini image + headshot + siatka 2×2 | wzór struktury skilla na **etap AI** (po 5–10 filmach) |
| [taoufik123-collab/thumbnail-generator](https://github.com/taoufik123-collab/thumbnail-generator) | face-swap na cudze miniatury | **nie** — kopiowanie cudzych miniatur (prawa autorskie, wizerunek) |

Zasada bezpieczeństwa: skill z GitHuba to prompt + kod wykonywany z naszymi uprawnieniami. Przed instalacją
czytamy całość, instalujemy w zakresie projektu, nigdy nie dajemy mu dostępu do kluczy w `~/.config/yt_channel/`.

## Priorytet 2 — później (płatne, po 5–10 filmach, zgodnie z decyzją z 2026-10-28)
- **Scena AI bez tekstu** (Gemini image z alertem budżetu albo FLUX Kontext przez API) + tekst zawsze
  z `thumbnail.py`; punkt kontrolny przed każdą partią.
- **IC-Light** (relighting twarzy pod tło) — potrzebuje GPU; na VPS bez GPU odpada, ewentualnie przez
  hostowane API za grosze za obraz.

## Proponowana kolejność prac
1. `thumbnail_check.py` (OCR 168×94, kontrast, strefa czasu, saliency, zgodność) + wpięcie w `yt-producer`.
2. Makieta feedu (dark/light, obok konkurencji) + krok krytyka wizualnego.
3. Test 3 fontów OFL → wybór fontu marki → `assets/fonts/`.
4. Ulepszenie twarzy: `birefnet-portrait`, dopasowanie koloru, obrys; nowa sesja zdjęć.
5. Render pierwszej strony publikacji jako karta `rich` (`pypdfium2`).
6. Test CoDesign w osobnej sesji (licencja, jakość, czy wnosi coś ponad nasz skrypt).

## Źródła
- Anthropic skills: https://github.com/anthropics/skills (canvas-design, Apache 2.0)
- IC-Light: https://github.com/lllyasviel/IC-Light
- CoDesign: https://img.ly/codesign/install/
- vidIQ MCP: https://vidiq.com/agent-skills/ , https://outlierkit.com/resources/vidiq-mcp/
- YouTube Test & Compare: https://support.google.com/youtube/answer/13861714
- Repozytoria skilli — linki w tabeli powyżej.
