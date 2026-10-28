# Research kanałów YouTube — październik 2026

_Dane: YouTube Data API v3, pobrane 2026-10-28 skryptem `scripts/yt_research.py` (ostatnie 50 filmów; Veritasium, MKBHD, QuantInsti, Paddy Galloway — 150). „Długie” = >3 min. Mediana liczona z długich filmów starszych niż 14 dni. „×” = wyświetlenia / mediana kanału. Wnioski: `docs/YT_PUBLISHING_STANDARD.md`._

| Kanał | Subskrypcje | Długie/mies. | Mediana długości [min] | Śr. dł. tytułu | Rozdziały | Napisy własne | Śr. linków | Śr. dł. opisu | Tagi |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| QuantPy | 97,700 | 0.8 | 21.1 | 65.8 | 27% | 2% | 4.3 | 2029 | 48% |
| Part Time Larry | 138,000 | 0.9 | 22.4 | 56.8 | 68% | 0% | 2.2 | 1552 | 48% |
| Algovibes | 139,000 | 10.8 | 11.9 | 53.8 | 2% | 0% | 1.7 | 1473 | 0% |
| QuantInsti Quantitative Learning | 46,100 | 2.8 | 8.9 | 75.0 | 97% | 0% | 6.1 | 3290 | 94% |
| Patrick Boyle | 1,360,000 | 4.4 | 32.0 | 39.8 | 0% | 18% | 12.6 | 1965 | 100% |
| Ben Felix | 654,000 | 1.7 | 16.2 | 36.9 | 31% | 0% | 9.9 | 1550 | 100% |
| The Plain Bagel | 1,220,000 | 2.3 | 18.0 | 43 | 46% | 0% | 1.3 | 834 | 2% |
| Paddy Galloway | 533,000 | 0.4 | 10.7 | 59.2 | 0% | 0% | 3.7 | 1626 | 94% |
| Veritasium | 21,400,000 | 2.5 | 31.1 | 44.0 | 86% | 100% | 12.5 | 3493 | 100% |
| Marques Brownlee | 21,400,000 | 5.2 | 11.9 | 37.8 | 19% | 99% | 6.9 | 412 | 88% |

## Najlepsze filmy względem mediany kanału

### QuantPy (mediana 16,695)
- ×24.42 — How Financial Firms Actually Make Money (22 min, 407,732 wyśw.)
- ×7.48 — Stochastic Calculus for Quants | Understanding Geometric Brownian Motion using Itô Calculus (22 min, 124,884 wyśw.)
- ×6.79 — A 20-Year Veteran Reveals the World of Options Market Making (52 min, 113,294 wyśw.)
- ×6.7 — Brownian Motion for Financial Mathematics | Brownian Motion for Quants | Stochastic Calculus (15 min, 111,842 wyśw.)
- ×3.77 — Monte Carlo Simulation for Option Pricing with Python (Basic Ideas Explained) (30 min, 62,904 wyśw.)

### Part Time Larry (mediana 24,637)
- ×6.95 — Why Kalshi Bettors Lose (72 Million Trades Analyzed) (16 min, 171,268 wyśw.)
- ×6.66 — Perplexity Finance: AI Tools, SEC API, Financial Data (17 min, 164,075 wyśw.)
- ×5.68 — 5. OpenAI Embeddings API - Searching Financial Documents (20 min, 139,957 wyśw.)
- ×5.02 — Automating Investment Research with Perplexity Finance - Tasks, Alerts, Earnings (22 min, 123,604 wyśw.)
- ×4.86 — 2. OpenAI Whisper - Fed Speech Recognition (22 min, 119,805 wyśw.)

### Algovibes (mediana 3,919)
- ×28.71 — I Trained an AI on 6.4 Million Candles. Then I Made It 190x Bigger. (13 min, 112,530 wyśw.)
- ×20.4 — Polymarket Knew Before Wall Street. So I Tried to Trade It. (11 min, 79,939 wyśw.)
- ×19.39 — Polymarket's Best Traders Keep Winning. So I Copied Them. (11 min, 75,996 wyśw.)
- ×17.29 — The Only Trading Strategy That Never Had a Losing Year (15 min, 67,757 wyśw.)
- ×12.94 — I Tried High-Frequency Trading From My Laptop (15 min, 50,722 wyśw.)

### QuantInsti Quantitative Learning (mediana 961)
- ×56.08 — Algorithmic Trading with Zerodha Kite Connect: Setting Up Your API Ecosystem (Part 2/5) (9 min, 53,894 wyśw.)
- ×30.2 — Algorithmic Trading in India with Zerodha Kite Connect: Complete Series Introduction (Part 1/5) (13 min, 29,021 wyśw.)
- ×17.25 — Advanced Order Types & Comprehensive Risk Management: Algo Trading with Zerodha (Part 5/5) (12 min, 16,578 wyśw.)
- ×14.77 — Future of Data, Trading & The Quant Industry with Decentralized AI (3 min, 14,196 wyśw.)
- ×12.74 — Kite Connect Core Trading Operations: Polling vs. WebSocket Ticker, Orders, Positions & Rate Limits (26 min, 12,246 wyśw.)

### Patrick Boyle (mediana 1,286,206)
- ×1.98 — Scott Bessent Is at War With Prices — and Prices Are Winning! (46 min, 2,543,777 wyśw.)
- ×1.91 — Is the AI Bubble About to Be Tested? (34 min, 2,452,531 wyśw.)
- ×1.9 — Why Germany Stopped Working (32 min, 2,450,208 wyśw.)
- ×1.85 — How Did the Metaverse Fail So Badly? (31 min, 2,377,309 wyśw.)
- ×1.72 — The Epstein Files are Worse Than You Think! (37 min, 2,209,783 wyśw.)

### Ben Felix (mediana 249,346)
- ×4.37 — Using Your Money To Be Happier (21 min, 1,089,985 wyśw.)
- ×4.14 — The Most Controversial Paper in Finance (23 min, 1,032,748 wyśw.)
- ×3.9 — Renting vs. Buying a Home: What People Get Wrong (18 min, 973,452 wyśw.)
- ×2.81 — The Biggest Myths in Personal Finance (20 min, 700,554 wyśw.)
- ×2.29 — The Rise of ETF Slop (18 min, 571,601 wyśw.)

### The Plain Bagel (mediana 244,363)
- ×4.97 — Let's Talk About the AI Bubble (22 min, 1,214,079 wyśw.)
- ×3.41 — Investment Analyst Reacts to Finance TikToks - Bonus Edition (29 min, 832,200 wyśw.)
- ×3.04 — Investment Analyst Reacts to Finance TikToks - Doomsday Doomscrolling (23 min, 743,888 wyśw.)
- ×2.94 — How BAD Are Stock Valuations Really? (18 min, 717,875 wyśw.)
- ×2.66 — Canada's Condo Conundrum (24 min, 650,689 wyśw.)

### Paddy Galloway (mediana 493,147)
- ×13.95 — How Beluga Gained 4 Million Subscribers in 3 Months (Genius Strategy) (10 min, 6,879,034 wyśw.)
- ×12.75 — Here’s why Mr Beast is a GENIUS - How He Grew his YouTube Channel (10 min, 6,286,486 wyśw.)
- ×7.93 — How MrBeast's Squid Game Broke YouTube (Genius Strategy) (9 min, 3,908,944 wyśw.)
- ×4.61 — How Mark Rober is beating the YouTube Algorithm (Genius Strategy) (10 min, 2,271,003 wyśw.)
- ×3.43 — How MR BEAST Built His Business Empire ($1 Billion on YouTube?) (10 min, 1,693,661 wyśw.)

### Veritasium (mediana 10,772,823)
- ×6.0 — The Closest Thing We Have to Alien Technology (55 min, 64,640,968 wyśw.)
- ×3.5 — White holes and wormholes are probably real. Here's why. (37 min, 37,700,571 wyśw.)
- ×3.46 — The Biggest Chemical Coverup In History (54 min, 37,325,680 wyśw.)
- ×2.94 — Can You Keep Zooming In Infinitely? (21 min, 31,646,239 wyśw.)
- ×2.45 — This Skyscraper Was Days From Collapsing And No One Knew (33 min, 26,363,757 wyśw.)

### Marques Brownlee (mediana 5,039,782)
- ×5.61 — iPhone 18 Pro/Duo Impressions: Mogged (17 min, 28,264,083 wyśw.)
- ×2.82 — Xiaomi 18 Pro Max: They've Done It Again! (11 min, 14,196,507 wyśw.)
- ×2.81 — iPhone 17/Pro/Air Impressions: Spot the Red Flags! (14 min, 14,139,783 wyśw.)
- ×2.6 — Driving Xiaomi's Electric Car: Are we Cooked? (17 min, 13,091,018 wyśw.)
- ×2.55 — iPhone Duo: What We Missed! (10 min, 12,830,556 wyśw.)

## Obserwacje jakościowe (miniatury i opisy)
- **Algovibes:** ciemna zieleń, 2–3 ogromne słowa + liczba + wykres, bez twarzy. Opis zaczyna się narracją eksperymentu z wynikiem, potem blok „📋 Method”. Tytuły „twierdzenie → test”.
- **QuantPy:** stockowe zdjęcia + żółto-biały tekst; najlepszy film to temat sceptyczny („Algorithmic Trading on YouTube is FAKE”). Tytuły z kreskami i upychaniem słów kluczowych.
- **Part Time Larry:** jasne plansze z logo narzędzi; najlepszy film to analiza danych z liczbą w tytule.
- **Ben Felix:** twarz + 2–4 słowa z jednym słowem w kolorze + zrzut publikacji/wykresu w tle. Opis: rozdziały, linki do bibliografii (zbib.org), podcast.
- **Patrick Boyle:** twarz + obiekt kontekstu + 2–3 słowa; opis zaczyna się od sponsora, 12+ linków (dużo skracaczy).
- **The Plain Bagel:** twarz + jeden symbol; krótki opis z pełnym disclaimerem.
- **Veritasium:** jedno zdanie serif + jeden obiekt; rozdziały prawie zawsze, źródła przez własne skrócone linki; napisy 100%.
- **MKBHD:** prawie bez tekstu, produkt w centrum; opis krótki, stały blok linków.
- **Paddy Galloway:** stały szablon serii (siatka, czarno-czerwony tekst, wycięta twarz) — rozpoznawalność od pierwszego rzutu oka.

## Ograniczenia
API nie daje CTR, utrzymania widza, źródeł ruchu, treści mówionej, plansz końcowych ani kart. Skuteczność oceniana pośrednio (wyświetlenia względem mediany kanału).
