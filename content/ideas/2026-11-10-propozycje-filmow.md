# Propozycje filmów — 2026-11-10

Źródła: `docs/CHANNEL_STRATEGY.md`, `context/feed/2026-W46.md`, karty `context/factory/` (README, funnel, lessons),
karty narzędzi z feedu: `context/tools/CurrencyExposureMonitor.md`, `context/tools/SpreadMonitorScalpers.md`.

**Proporcja:** 3 tematy z projektów (fabryka EA) + 2 evergreen (Tools, Validation Gates) = 60/40 w tej partii.
Temat 5 korzysta z jednego przypadku z fabryki jako przykładu, więc w praktyce partia jest bliżej 70/30.
Po zdjęciu embarga (od 19.11) dochodzą kolejne tematy z projektów — patrz „Po embargo” na końcu.

**Każdy film z liczbami:** disclaimer *„Historical results, not investment advice. Past performance does not
guarantee future results.”* Wszystkie liczby poniżej pochodzą z kart; „brak danych” = karta ich nie podaje.

---

## 1. Martwy warunek wejścia (z projektu)

- **Tytuł roboczy:** *Zero Trades: How to Find an Entry Condition That Can Never Be True*
- **Filar:** Validation Gates (bramka 1: Data & logic integrity), na przykładzie zdarzenia z fabryki
- **Źródło:** `context/factory/lessons/2026-10-13-martwy-warunek-wejscia.md`; feed W46, commit `e4b2d56`
  (lekcja „zero transakcji to prawie zawsze błąd implementacji”)
- **Wolno publikować od:** 2026-11-03 (już można)
- **Hak (EN, 0–15 s):** *“This strategy passed code review. It compiled. Then it ran on almost twenty-five thousand
  candles and opened zero trades. Not because it was careful — because one of its conditions could never be true.”*

**Formuła:**
1. **Co się wydarzyło:** strategia breakoutowa z publikacji przeszła audyt i kompilację, a w backteście dała
   0 transakcji. Bramka smoke zgłosiła 0 wejść tylko jako ostrzeżenie, więc kod poszedł dalej. Przyczyny: pasmo
   liczone wokół bieżącego zamknięcia (`close > close + σ` — niemożliwe) połączone przez AND oraz „VWAP + średnia”
   odczytane jako suma dwóch cen.
2. **Dlaczego to dotyczy widza:** zero transakcji to prawie zawsze błąd implementacji, a nie „ostrożna strategia”.
   Objaw łatwo wykryć, ale do naprawy trzeba wiedzieć, który człon warunku jest martwy. Automatyczna poprawka, która
   dostawała tylko informację „0 wejść”, nie naprawiła żadnego przypadku.
3. **Jak sprawdzić u siebie:** losowy spacer cen (kilka tysięcy świec) i licznik trafień dla każdego członu warunku
   osobno. Człon z 0 trafień = martwy kod. Drugi skrajny sygnał ostrzegawczy: wejścia na > 15% świec.
4. **Werdykt i liczby:** dane syntetyczne 24 768 świec → 0 wejść; bramka wykryła 5 przypadków (13–22.10),
   automatycznie naprawiono 0/5; typowa strategia na tych samych danych daje sygnał na 0–4% świec. Werdykt bramki:
   0 wejść = FAIL, zatrzymuje dalszą ocenę.

**Rozdziały (orientacyjnie):**
- 0:00 Zero trades on 24,768 candles
- 0:45 The impossible condition (`close > close + σ`)
- 2:30 Why “no trades” is a bug, not caution
- 4:00 Test it yourself: random walk + per-condition counter
- 6:30 What the gate does now (5 caught, 0 auto-fixed)
- 8:00 Verdict

**Na ekranie:** schemat bramki smoke (dane syntetyczne → liczba wejść → poprawka / przepuszczenie), pseudokod
`close > close + σ` jako ilustracja, licznik 5 wykrytych / 0 naprawionych, własny prosty skrypt Python z losowym
spacerem i licznikiem członów (napisany od zera do filmu).
**NIE pokazywać:** promptu generatora ani promptu poprawki, wygenerowanego kodu strategii, ścieżek w magazynie
plików. W tytule i miniaturze nie używać słowa „AI” (w skrypcie mówić o „automatic fix”).

---

## 2. Pięć strategii, jeden pomysł (z projektu)

- **Tytuł roboczy:** *Five Strategies, One Idea: Why I Count Ideas, Not Names*
- **Filar:** Validation Gates (bramka 6: Overfitting — liczba prób), na przykładzie zdarzenia z fabryki
- **Źródło:** `context/factory/lessons/2026-10-14-limit-wariantow-jednego-pomyslu.md`; feed W46, commit `e4b2d56`
  (lekcja „warianty jednego pomysłu to jedna hipoteza testowana wielokrotnie”)
- **Wolno publikować od:** 2026-11-04 (już można)
- **Hak (EN):** *“In one night my research pipeline found five strategies from five different sources. Different
  names, different authors. It was the same idea five times — and testing it five times quietly raises the chance
  of a lucky result.”*

**Formuła:**
1. **Co się wydarzyło:** research znalazł 5 strategii pod różnymi nazwami. Wszystkie to przełączanie reżimu według
   wykładnika Hursta na tym samym rynku i interwale. Deduplikacja porównywała tylko nazwy, więc niczego nie złapała.
2. **Dlaczego to dotyczy widza:** pięć wariantów to jedna próba wykonana pięć razy (problem wielokrotnego
   testowania). Każdy dodatkowy wariant zwiększa szansę na przypadkowy „sukces”.
3. **Jak sprawdzić u siebie:** pogrupuj testowane strategie po (mechanizm, rynek, interwał) i policz warianty
   w grupie. Wszystkie warianty wliczaj do statystyki (np. Deflated Sharpe).
4. **Werdykt i liczby:** 5 wariantów w jednej nocy; 1 odpadł w generatorze, 4 w backteście, 0 przeszło. Poprawka:
   klucz pomysłu = styl + rynek + interwał, limit 2 wariantów pomysłu na noc.

**Rozdziały:**
- 0:00 Five names, one idea
- 0:50 How name-based dedup failed
- 2:30 Multiple testing in plain words
- 4:30 Test it yourself: group by mechanism, market, timeframe
- 6:30 The fix: idea key + 2 variants per night
- 7:30 Verdict: 5 in, 0 survived

**Na ekranie:** lista 5 nazw obok jednego klucza pomysłu (bez reguł strategii), schemat nazwa → klucz pomysłu →
limit, prosta wizualizacja „więcej prób = większa szansa na przypadkowy wynik” (bez liczb spoza kart, raczej schemat
niż wykres z danymi).
**NIE pokazywać:** promptów researchu i ekstrakcji, pełnych opisów strategii z JSON-ów, parametrów.

---

## 3. Bitcoin policzony jak para walutowa (z projektu)

- **Tytuł roboczy:** *My Backtester Treated Bitcoin Like EUR/USD — 29% of the Data Was Missing*
  (liczba realna z karty i opisuje proces; jeśli ma być bez liczby: *Your Backtester Has Hidden Assumptions About the Market*)
- **Filar:** Validation Gates (bramka 2: Backtest integrity), na przykładzie zdarzenia z fabryki
- **Źródło:** `context/factory/lessons/2026-10-07-krypto-w-silniku-fx.md`; feed W46, commit `e4b2d56`
  (lekcja „backtester ma ukryte założenia o rynku”)
- **Wolno publikować od:** 2026-10-28 (już można)
- **Hak (EN):** *“The backtest looked normal. Reasonable trades, reasonable costs. But the engine thought Bitcoin was
  a currency pair — so it charged forex costs and deleted every weekend.”*

**Formuła:**
1. **Co się wydarzyło:** przegląd nocnego backtestu BTCUSD pokazał, że silnik policzył go profilem forex. Każdy
   6-literowy symbol trafiał do forex (koszty, swap, punkt 0,00001), a agregacja świec wycinała weekendy. Wynik
   unieważniony, przebieg do powtórki.
2. **Dlaczego to dotyczy widza:** backtester ma ukryte założenia (godziny handlu, koszty, punkt, swap). Przeniesienie
   strategii na inną klasę aktywów bez zmiany tych założeń daje liczby, które wyglądają wiarygodnie, a są błędne.
3. **Jak sprawdzić u siebie:** policz świece na dzień tygodnia w danych wejściowych (24/7 vs 24/5); wypisz koszt jednej
   transakcji w walucie konta i porównaj ze specyfikacją u brokera. Rollover krypto: 7 dni w tygodniu, nie 5.
4. **Werdykt i liczby:** brakujące świece BTC przed poprawką: ok. 29%; świece w środku weekendu w realnych danych:
   BTC 25%, EURUSD M1 0% (próg rozpoznania rynku 24/7: 5%); testy silnika po poprawce: 146 (28 nowych). Werdykt:
   wynik nieważny (FAIL integralności backtestu), nie „słaba strategia”.

**Rozdziały:**
- 0:00 A normal-looking backtest that was wrong
- 0:45 Bitcoin as a six-letter forex symbol
- 2:15 The missing weekends (29%)
- 4:00 Hidden assumptions every backtester makes
- 5:30 Test it yourself: candles per weekday + cost per trade
- 7:30 Verdict and the fix

**Na ekranie:** wykres liczby świec na dzień tygodnia BTC vs EURUSD, tabela profili kosztów forex vs krypto
(sama struktura, bez wartości kalibracji brokera), prosty skrypt liczący świece na dzień tygodnia.
**NIE pokazywać:** nazwy brokera, konfiguracji serwerów i adresów, wartości kalibracji kosztów.

---

## 4. Currency Exposure Monitor (evergreen, Tools)

- **Tytuł roboczy:** *Four Trades or One Bet? A Free MT5 Currency Exposure Monitor*
- **Filar:** Tools
- **Źródło:** `context/tools/CurrencyExposureMonitor.md`; feed W46, commit `521b17b` (opublikowany w CodeBase
  2026-10-29, https://www.mql5.com/en/code/78944)
- **Wolno publikować od:** od razu (narzędzie publiczne, brak embarga)
- **Hak (EN, z karty):** *“Four different trades — or one big bet against the dollar? Your position list won't tell you.”*

**Formuła:**
1. **Co się wydarzyło:** dopisałem do darmowych narzędzi w CodeBase monitor ekspozycji walutowej i dźwigni (odpowiednik
   iExposure z MT4, którego brakuje w MT5).
2. **Dlaczego to dotyczy widza:** ryzyko siedzi w walutach, a nie w symbolach. Kilka pozycji na różnych parach może
   być jednym dużym zakładem na jedną walutę.
3. **Jak sprawdzić u siebie:** demo 60 s z karty: EURUSD buy, GBPUSD buy, USDJPY sell, XAUUSD buy → słupek USD;
   efektywna dźwignia i sekcja „If one rises 1.0%”; podpowiedź przy wierszu USD; scena „ukryty EURCHF”
   (EURUSD + USDCHF buy); zmiana wrażliwości na 2%.
4. **Werdykt i liczby:** brak danych z Ledgera; to film narzędziowy. Na ekranie pokazujemy wartości, które
   wskaźnik faktycznie wyświetli w dniu nagrania. **Uwaga:** wartości z karty (12.9 : 1, −12,8% equity) są oznaczone
   „np.”, więc to przykład. Nie czytamy ich w skrypcie i nie dajemy do tytułu ani miniatury.
   Uczciwe ograniczenia z karty: wrażliwość liniowa bez korelacji, swapów i prowizji; zlecenia oczekujące nieliczone
   (planowane w v1.10, CEM-110); indeksy i towary CFD jako wiersz „aktywa”.

**Rozdziały (4–7 min):**
- 0:00 Four trades or one bet?
- 0:30 The demo: one hidden USD position
- 2:00 Effective leverage and the 1% sensitivity
- 3:00 The hidden EURCHF trade
- 4:00 Under the hood: splitting positions into currency legs
- 5:15 Limitations and where to get it

**Na ekranie:** panel w scenach „jeden zakład” i „ukryty EURCHF”, okno inputów (filtr magic, % wrażliwości, progi),
kod `CurrencyExposureMonitor.mq5`: `AddPosition()`, `PositionNotional()`, `CurrencyRate()`.
**NIE pokazywać:** numeru konta, nazwy brokera i serwera, realnego konta, linków do innych produktów, profilu jako
„oferty”, niczego z prac dla innych osób (inne okna MetaEditora). CTA: link do CodeBase i profil mql5.com.
**Short:** scena „4 pozycje → 1 słupek USD” (≤ 30 s).

---

## 5. Profit Factor i przypadki brzegowe (evergreen, Validation Gates)

- **Tytuł roboczy:** *Win Rate Tells You Almost Nothing — and Profit Factor Can Break Your Validation*
  (krócej: *When 0 / 0 Rejected a Perfect Match*)
- **Filar:** Validation Gates (bramka 3: Performance), przypadek z fabryki jako przykład
- **Źródło:** `context/factory/lessons/2026-10-14-parytet-pf-zero-przez-zero.md`; feed W46, commit `e4b2d56`
  (lekcja „metryki-ilorazy mają przypadki brzegowe (0/0)”)
- **Wolno publikować od:** 2026-11-04 (już można)
- **Hak (EN):** *“Two engines. Eight trades each. Identical results, trade for trade. And my validation gate rejected
  them for not matching. The reason was a division: zero divided by zero.”*

**Formuła:**
1. **Co się wydarzyło:** bramka parytetu (EA w MT5 vs model w Pythonie) odrzuciła strategię za niezgodny PF, choć obie
   implementacje dały to samo. Iloraz PF_MT5 / PF_Python = 0 / 0 wypadał „poza zakresem [0,8; 1,25]”.
2. **Dlaczego to dotyczy widza:** każda metryka-iloraz (PF, Sharpe, Recovery) ma przypadki brzegowe: 0 / 0, x / 0,
   mała próbka. Evergreenowa część: co naprawdę mówią win rate, PF, expectancy i liczba transakcji, i dlaczego
   sama liczba bez kontekstu próbki niczego nie dowodzi.
3. **Jak sprawdzić u siebie:** przepuść przez swoją bramkę trzy sztuczne logi: same zyski, same straty, zero
   transakcji. NaN / inf albo decyzja bez uzasadnienia = dziura w bramce.
4. **Werdykt i liczby:** MT5 8 / Python 8 transakcji; zyskowne 0 / 0; PF 0 / 0; WR 0% / 0%. Poprawka: przy obu PF = 0
   parytet oceniany po znaku średniej transakcji. Testy bramki po poprawce: 15 (3 nowe). Pozostałe liczby (np.
   progi PF czy minimalna liczba transakcji w metodologii): brak danych, więc ich nie podajemy.

**Rozdziały:**
- 0:00 Identical results, rejected anyway
- 0:40 Profit Factor in one formula
- 2:00 The 0 / 0 trap
- 3:30 Win rate, PF, expectancy: what each one hides
- 6:00 Test your own gate: three fake trade logs
- 8:00 Verdict

**Na ekranie:** tabelka MT5 vs Python (transakcje, WR, PF) dla tego przypadku, wzór PF i trzy przypadki brzegowe,
trzy sztuczne logi przepuszczone przez prostą funkcję w Pythonie (napisaną do filmu).
**NIE pokazywać:** kodu i parametrów strategii. Strategia jest odrzucona, ale nie ma karty graveyard, więc nie
pokazujemy jej logiki ani nazwy.

---

## Sugerowana kolejność publikacji

1. Temat 3 (Bitcoin / 29%): najmocniejszy hak, embargo dawno minęło.
2. Temat 4 (Tools, Currency Exposure Monitor): świeża publikacja w CodeBase.
3. Temat 1 (martwy warunek wejścia).
4. Temat 2 (pięć strategii, jeden pomysł). Dobrze przygotowuje grunt pod pierwszy raport lejka.
5. Temat 5 (PF 0 / 0).

## Po embargo (nie czytane treściowo, tylko daty)

| Karta | Publikacja od | Potencjał |
|---|---|---|
| `context/factory/funnel/2026-10.md` | 2026-11-19 | pierwszy odcinek **The Funnel** (raport października) |
| `context/factory/lessons/2026-11-05-ryzyko-dziesiec-razy-za-duze.md` | 2026-11-26 | lekcja o wielkości pozycji |
| `context/factory/lessons/2026-11-07-paper-bez-transakcji-symbol-wylaczony.md` | 2026-11-28 | lekcja z paper tradingu |
| `context/factory/lessons/2026-11-09-profit-factor-11-z-jednej-pozycji.md` | 2026-11-30 | naturalna kontynuacja tematu 5 |

## Rezerwa evergreen

- **SpreadMonitorScalpers v1.32** (`context/tools/SpreadMonitorScalpers.md`, feed `2232620`): film Tools albo
  ilustracja do bramki 7 (Execution: stres spreadu). Liczby: brak danych. Hak z karty: *“Your scalping strategy
  might be fine — it's the spread you never see that's eating your profits.”*
