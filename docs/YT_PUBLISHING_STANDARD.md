# Standard publikacji YouTube

_Wersja 1.0 — 2026-10-28. Źródła: YouTube Data API (10 kanałów, ~600 filmów, skrypt `scripts/yt_research.py`),
oficjalna pomoc YouTube i poradniki. Raport z badania: `docs/research/2026-10-yt-kanaly.md`. Odświeżać co kwartał._

Ten dokument obowiązuje razem z `docs/CHANNEL_STRATEGY.md` (granice treści i języka mają pierwszeństwo).
Korzysta z niego agent `yt-producer` (komenda `/publikacja`).

## 1. Twarde reguły YouTube (oficjalne)
| Element | Reguła | Źródło |
|---|---|---|
| Rozdziały | pierwszy timestamp `0:00`, min. 3 rosnąco; my dodatkowo min. 10 s na rozdział | YouTube Help 9884579 |
| Opis | max 5000 znaków; bez rozwijania widać ~100–150 znaków | YouTube Help 12948449 + źródła wtórne |
| Plansza końcowa | ostatnie 5–20 s, film ≥ 25 s, max 4 elementy; nie wyświetla się w mobilnej przeglądarce | YouTube Help 6388789 |
| Miniatura | 1280×720 (16:9), ≤ 2 MB, JPG/PNG | źródła wtórne zgodne |
| Hashtagi | 3 pierwsze nad tytułem; >60 = wszystkie ignorowane (niepotwierdzone oficjalnie) | źródła wtórne |

## 2. Tytuł
**Dane:** kanały milionowe mają średnio **37–44 znaki**, nisza algo 54–75. Najlepsze filmy w niszy (wyświetlenia
względem mediany kanału) to tytuły sceptyczne z twardą liczbą i testem w 1. osobie:
- „ICT Traders Swear This Works. I Tested the Numbers.” / „You Found a Strategy That Works. I Have Bad News.” (Algovibes)
- „Why Kalshi Bettors Lose (72 Million Trades Analyzed)” (Part Time Larry, ×7 mediany)
- „The Most Controversial Paper in Finance” (Ben Felix, ×4,1) — publikacja jako bohater filmu
- „How Financial Firms Actually Make Money” (QuantPy, ×24)

**Reguły:**
1. Długość docelowo **40–55 znaków**, twardy limit 60. Najważniejsze słowa w pierwszych 40 znakach.
2. Wzorce (wybierz jeden):
   - **Twierdzenie → test:** „<Claim people make>. I Tested It.”
   - **Liczba jako dowód:** „<Wniosek> (<realna liczba> <jednostka> Tested)”
   - **Publikacja jako bohater:** „This Paper Claims <X>. Does It Survive Costs?”
   - **Pytanie z napięciem:** „Why <grupa> <wynik>” / „How <X> Actually <Y>”
3. Liczby wyłącznie z Ledgera / kart. Bez pionowych kresek i upychania słów kluczowych
   (wzór do unikania: „Brownian Motion for Financial Mathematics | Brownian Motion for Quants | …”).
4. Zakazane słowa i język sprzedaży — `CHANNEL_STRATEGY.md` §7 (uwaga: „The Only Trading Strategy…” u Algovibes
   działa, ale „only” jest u nas zakazane).
5. Tytuł i tekst na miniaturze **uzupełniają się**, nie powtarzają.
6. Zawsze 3–5 wariantów; jeśli YouTube Studio udostępnia Test & Compare — testować 2–3.

## 3. Miniatura
**Obserwacje (top filmy):**
- **Ben Felix** (najbliższy nam): twarz + 2–4 słowa, jedno słowo w kolorze akcentu, w tle **zrzut publikacji
  lub wykresu** → idealny wzór dla „Paper vs Reality”.
- **Algovibes:** ciemne tło, stały kolor marki (zieleń), 2–3 ogromne słowa + jedna liczba + wykres. Bez twarzy.
- **Patrick Boyle / The Plain Bagel:** twarz + jeden obiekt kontekstu + 2–3 słowa (albo zero słów).
- **Veritasium:** jedno krótkie zdanie (serif) + jeden uderzający obiekt; minimum tekstu.
- **MKBHD:** prawie bez tekstu, jeden obiekt, czystość.
- **Paddy Galloway:** stały szablon serii (siatka, czarno-czerwony tekst, wycięta twarz z obrysem) → rozpoznawalność.

**Nasz szablon (render: `scripts/thumbnail.py`):**
1. Układ: **tekst po lewej (≈55%), twarz po prawej (≈40%)**; bez twarzy — duża liczba/wykres po prawej.
2. Tekst: **2–4 słowa**, max 2 linie, jedno słowo w kolorze akcentu. Font: wąski, bold.
3. Tło: ciemne (granat/grafit) + **motyw tradingowy** (`--motif`): krzywa equity z podziałem IN-SAMPLE /
   OUT-OF-SAMPLE (fail = załamanie po OOS, pass = wzrost), świece albo słupki lejka. Kluczowy fragment (podział,
   załamanie) zawsze między tekstem a twarzą; strona tekstu przyciemniona. Motyw syntetyczny = dekoracja bez
   liczb i osi z wartościami; realny przebieg tylko z danych karty (`--equity-csv`).
4. Kolor marki stały w każdej miniaturze (akcent: zieleń „PASS” / czerwień „FAIL” — kolor = werdykt).
5. Czytelność sprawdzana na podglądzie **168×94** (rozmiar z listy na telefonie).
6. Seria = rozpoznawalny element: etykieta filaru w rogu (np. `GRAVEYARD`, `PAPER vs REALITY`, `FUNNEL #3`).
7. Bez: strzałek-clickbaitów, przesadnej mimiki, kwot zysku, „$$$”, logo brokerów.
8. **Warianty i test A/B:** 3–4 warianty w różnych archetypach (twarz + tekst / liczba bez twarzy / publikacja
   w tle / pytanie), siatka podglądu (`scripts/thumbnail_grid.py`), 3 najlepsze do Test & Compare w YouTube Studio.
   Zwycięzcę po kilku filmach zatwierdzamy jako **miniaturę-matkę** (`assets/style/master.jpg`) — wzór stylu.
9. **Generowanie obrazów AI — wyłączone** (decyzja 2026-10-28, start za 0 zł; Gemini image nie ma darmowego
   limitu). Wracamy do tematu po 5–10 filmach: płatności w Google Cloud z alertem budżetu, AI tylko do sceny
   bez tekstu, tekst zawsze z `thumbnail.py`, obowiązkowy punkt kontrolny przed każdą płatną partią.
   Analiza podejścia: `content/ideas/2026-10-28-analiza-miniatury-higgsfield.md`.

## 4. Opis
**Dane:** milionowe kanały mają 7–12 linków i 2000–3500 znaków (Veritasium), MKBHD celowo krótko (~400).
Algovibes otwiera opis narracją eksperymentu z wynikiem i ma blok **„📋 Method”** (dane, okres, instrumenty).
Ben Felix i Veritasium podają **źródła/bibliografię**. The Plain Bagel ma pełny disclaimer.

**Struktura (kolejność obowiązkowa):**
```
1. Hak (≤150 znaków): co testowałem i jaki był wynik/napięcie — 1–2 zdania, 1. osoba.
2. Rozwinięcie (2–4 zdania).
3. 📋 Method: dane (rynek, interwał, okres), koszty, OOS/WFA, liczba prób.
4. Chapters: 0:00 … (min. 3, ≥10 s).
5. 📄 Sources: publikacje (autorzy, tytuł, rok, DOI/link) i inne źródła.
6. 🔬 Research lab: Methodology / Research Ledger (QuantInvest).
7. 🛠 Free tools: MQL5 Code Base / profil mql5.com.
8. ✉️ Newsletter (miesięczny raport lejka).
9. Subtitles: English, Polski.
10. Disclaimer (pełny).
11. Hashtagi: 0–3 (np. #algotrading #backtesting #quant).
```
- Linki pełne (bez skracaczy typu tinyurl/goo.gl), wyłącznie niesprzedażowe w fazie zaufania.
- Bez sponsorów do odwołania (sprzeczne z fazą zaufania).

## 5. Rozdziały
Veritasium 86% filmów, QuantInsti 97%, Part Time Larry 68%; Boyle i Galloway 0%. **U nas 100%**, nazwy
rozdziałów opisowe (np. „The paper's claim”, „Adding real costs”), nie „Part 2”.

## 6. Napisy
Veritasium 100%, MKBHD 99% — **kanały finansowe i algo ~0%**. Nasze napisy EN (wierne nagraniu) + PL to
wyróżnik w niszy i pomoc dla widzów nie-anglojęzycznych. Wgrywamy własne `.srt`, nie polegamy na automatycznych.

## 7. Tagi i hashtagi
Kanały milionowe używają tagów prawie zawsze (88–100%), nisza rzadko. Tagi mają małą wagę, ale są tanie:
**8–15 tagów** (temat, synonimy, nazwy metod, warianty pisowni). Hashtagi: 0–3.

## 8. Długość i rytm
- Długie filmy w niszy i finansach: mediana **11–22 min** (Ben Felix 16, Plain Bagel 18, Boyle 32).
  Start 6–10 min (nauka warsztatu), docelowo **10–18 min** dla filmów analitycznych.
- Rytm: Ben Felix 1,7/mies. (654 tys. subskrypcji), Plain Bagel 2,3, Algovibes 10,8. Nasze 1/tydz. mieści się
  w zakresie — jakość > częstotliwość.
- Serie numerowane działają (najlepsze filmy QuantInsti to „Part 1/5, 2/5…”): numerujemy filary
  („The Funnel #3”, „Graveyard #2”) i trzymamy je w playlistach.
- Shorts nie ratują słabego opakowania (QuantInsti: mediana Shorts ~1000 wyświetleń). 3–5 shorts z filmu
  jako zwiastun, każdy z linkiem do pełnego filmu.

## 9. CTA (subskrypcja i „kciuk w górę”)
Nie da się tego zmierzyć przez API — reguły z poradników i z naszej fazy zaufania:
1. **Jedno krótkie CTA głosem po dostarczeniu wartości**, nie na starcie. Moment: zaraz po kluczowym wniosku
   albo przed werdyktem. Wzór: *„If this kind of testing is useful, subscribe — every month I publish what
   survived and what didn't. And a like helps the video reach other systematic traders.”*
2. Na końcu (plansza 5–20 s): **subskrypcja + następny film/playlista filaru**, głosem — bo w mobilnej
   przeglądarce plansza się nie pokazuje.
3. **Przypięty komentarz:** pytanie do widzów (np. „Which strategy should go through the pipeline next?”)
   — bez linków sprzedażowych.
4. Nigdy: „smash the like”, CTA w pierwszych 30 s, prośby o subskrypcję w tytule/miniaturze.

## 10. Checklista publikacji (agent `yt-producer` ją wypełnia)
- [ ] Tytuł 40–55 znaków, wzorzec z §2, bez zakazanych słów, 3–5 wariantów.
- [ ] Miniatury: 3–4 warianty, siatka, faworyt + 3 do A/B; 1280×720 JPG ≤2 MB, 2–4 słowa, test 168×94, etykieta filaru.
- [ ] Opis wg §4, rozdziały `0:00` (min. 3), źródła, disclaimer, linki niesprzedażowe.
- [ ] Napisy EN + PL (`.srt`).
- [ ] Tagi 8–15, hashtagi 0–3.
- [ ] CTA głosem w skrypcie (§9) + plansza końcowa + przypięty komentarz.
- [ ] Playlista filaru, numer odcinka.
- [ ] 3–5 shorts z linkiem do filmu.
- [ ] Embargo karty źródłowej minęło.
