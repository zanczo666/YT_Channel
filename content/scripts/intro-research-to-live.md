---
slug: intro-research-to-live
filar: Intro (poza filarami; otwiera kanał)
zrodlo: content/ideas/2026-10-21-plan-startowy.md (film #1, Intro); brak karty z fabryki, wiedza ogólna
publish_after: brak
tytul_roboczy: I Test Trading Strategies in Public. Failures Included.
dlugosc_docelowa: 6–8 min
slowa_szacunkowo: 983 (≈ 6:45–7:00 przy 140–145 słowach/min)
---

> **Wersja:** twarz do kamery + plansze (diagram pipeline'u, zasady kanału) + zrzuty MT5 **bez wyników, nazw
> strategii i treści generatora**. Film celowo **bez żadnych liczb** (Ledger jeszcze nie jest publiczny).
> Nie wymieniamy QuantInvest i nie linkujemy quantinvest.co. CTA: subskrypcja + profil mql5.com.
>
> Warianty tytułu (do wyboru przez `yt-producer`, wszystkie 40–57 znaków, bez zakazanych słów):
> 1. I Test Trading Strategies in Public. Failures Included. (55)
> 2. From Research Paper to Live Algorithm, Failures Included (57)
> 3. How I Test Trading Ideas Before They Go Live (44)
> 4. Profitable Backtests Are Easy to Sell. I Test Them. (51)

## [0:00] Hook
<!-- 15 s: konflikt — kanały pokazują sukcesy, ja pokazuję porażki. Twarz. -->
| ID | EN (mówione) | PL (napisy) | Na ekranie |
|---|---|---|---|
| L001 | Most trading channels show you what worked. | Większość kanałów o tradingu pokazuje Ci, co zadziałało. | TWARZ |
| L002 | I'm going to show you what didn't, and why. | Ja pokażę Ci, co nie zadziałało, i dlaczego. | TWARZ: AKCENT |
| L003 | Every failure I publish is one mistake you don't have to make yourself. | Każda porażka, którą publikuję, to jeden błąd, którego nie musisz popełniać sam. | TWARZ |

## [0:12] Who I am and what this channel is
<!-- Kim jestem, czym jest kanał, co widz wyniesie z tego filmu. -->
| ID | EN (mówione) | PL (napisy) | Na ekranie |
|---|---|---|---|
| L004 | My name is Radoslaw Lubas. | Nazywam się Radosław Lubas. | BELKA: imie |
| L005 | I build trading systems, and I write their code myself. | Buduję systemy tradingowe i sam piszę ich kod. | TWARZ |
| L006 | I work in MQL5, the language of MetaTrader, and in Python. | Pracuję w MQL5, języku MetaTradera, oraz w Pythonie. | EKRAN: MT5 — czysty wykres na koncie demo, bez EA, bez Nawigatora i numeru konta |
| L007 | On this channel, I build and stress-test these systems in public. | Na tym kanale publicznie buduję te systemy i poddaję je testom w trudnych warunkach. | TWARZ |
| L008 | The path goes from research papers all the way to live algorithms. | Droga prowadzi od publikacji naukowych aż do algorytmów działających na żywym rynku. | — |
| L009 | And I publish the systems that fail, not just the ones that work. | I publikuję systemy, które odpadają, a nie tylko te, które działają. | — |
| L010 | This first video is the map of that path. | Ten pierwszy film to mapa tej drogi. | TWARZ |
| L011 | You'll see every step, the rules of this channel, and what comes next. | Zobaczysz każdy krok, zasady tego kanału i to, co będzie dalej. | — |
| L012 | If you test strategies yourself, you can use the same steps in your own work. | Jeśli sam testujesz strategie, możesz użyć tych samych kroków we własnej pracy. | TWARZ |

## [0:53] The pipeline: from paper to live
<!-- Krok 1 formuły: co u mnie działa i jak. Diagram budowany etap po etapie (jedna grafika, kolejne podświetlenia). -->
| ID | EN (mówione) | PL (napisy) | Na ekranie |
|---|---|---|---|
| L013 | Let me show you how an idea travels through my pipeline. | Pokażę Ci, jak pomysł przechodzi przez mój pipeline. | GRAFIKA: diagram pipeline'u — cały, wszystkie etapy wyszarzone |
| L014 | A pipeline is simply a fixed order of steps. | Pipeline to po prostu stała kolejność kroków. | — |
| L015 | Every idea goes through the same steps, in the same order. | Każdy pomysł przechodzi przez te same kroki, w tej samej kolejności. | — |
| L016 | Step one is research. | Krok pierwszy: badania. | GRAFIKA: diagram — podświetlony etap „Research” |
| L017 | I start with a published paper or a clear observation about the market. | Zaczynam od opublikowanej pracy naukowej albo od jasnej obserwacji rynku. | — |
| L018 | I write it down as a hypothesis: one claim that a test can reject. | Zapisuję ją jako hipotezę: jedno twierdzenie, które test może odrzucić. | — |
| L019 | A hypothesis is not a strategy yet. | Hipoteza to jeszcze nie strategia. | — |
| L020 | It's a question I want the market to answer. | To pytanie, na które ma odpowiedzieć rynek. | TWARZ |
| L021 | Step two is the code. | Krok drugi: kod. | GRAFIKA: diagram — podświetlony etap „Code (EA generator)” |
| L022 | A code generator turns the hypothesis into an Expert Advisor. | Generator kodu zamienia hipotezę w Expert Advisora. | — |
| L023 | An Expert Advisor, or EA, is a trading program that runs inside MetaTrader. | Expert Advisor, w skrócie EA, to program handlujący, który działa wewnątrz MetaTradera. | — |
| L024 | Before any real test, the EA gets a simple check. | Zanim zacznie się prawdziwy test, EA przechodzi prostą kontrolę. | — |
| L025 | Does it place trades at all, and do they follow the rules? | Czy w ogóle otwiera transakcje i czy są one zgodne z regułami? | — |
| L026 | An EA that never trades is usually a bug, not a careful strategy. | EA, które nigdy nie handluje, to zwykle błąd, a nie ostrożna strategia. | TWARZ |
| L027 | Step three is the backtest in MetaTrader five. | Krok trzeci: backtest w MetaTraderze 5. | EKRAN: MT5 Strategy Tester, zakładka Settings (nazwa EA zasłonięta, bez zakładek wyników) |
| L028 | A backtest replays the strategy on historical prices. | Backtest odtwarza strategię na cenach historycznych. | — |
| L029 | It answers one question: what would have happened in the past? | Odpowiada na jedno pytanie: co by się stało w przeszłości? | — |
| L030 | That's useful, but it's also where most mistakes hide. | To przydatne, ale właśnie tam kryje się najwięcej błędów. | TWARZ |
| L031 | Step four is a second engine, written in Python. | Krok czwarty: drugi silnik, napisany w Pythonie. | GRAFIKA: diagram — podświetlony etap „Python backtest” (dwa silniki obok siebie) |
| L032 | I run the same logic outside MetaTrader, with my own code. | Uruchamiam tę samą logikę poza MetaTraderem, na własnym kodzie. | — |
| L033 | If the two engines disagree, something is wrong. | Jeśli oba silniki się nie zgadzają, coś jest nie tak. | — |
| L034 | Sometimes the bug is in the strategy. | Czasem błąd jest w strategii. | — |
| L035 | Sometimes it's in the tester itself. | Czasem w samym testerze. | TWARZ |
| L036 | Step five is validation. | Krok piąty: walidacja. | GRAFIKA: diagram — podświetlony etap „Validation gates” |
| L037 | Here the strategy goes through a series of gates. | Tu strategia przechodzi przez serię bramek. | — |
| L038 | Each gate asks one hard question. | Każda bramka zadaje jedno trudne pytanie. | — |
| L039 | Does it survive higher spread and slippage? | Czy przetrwa wyższy spread i poślizg? | — |
| L040 | Those are the hidden costs between the price you see and the price you get. | To ukryte koszty między ceną, którą widzisz, a ceną, którą dostajesz. | — |
| L041 | Does it work on data it has never seen? | Czy działa na danych, których nigdy nie widziała? | — |
| L042 | We call that out-of-sample data. | Nazywamy to danymi spoza próby, czyli out-of-sample. | — |
| L043 | Is the result stable when I change the settings a little? | Czy wynik jest stabilny, gdy trochę zmienię ustawienia? | — |
| L044 | And how many versions did I try before this one looked good? | I ile wersji wypróbowałem, zanim ta zaczęła wyglądać dobrze? | — |
| L045 | Each gate gives a verdict: pass, conditional, or fail. | Każda bramka wydaje werdykt: PASS, CONDITIONAL albo FAIL. | GRAFIKA: trzy etykiety PASS / CONDITIONAL / FAIL |
| L046 | One critical fail stops the whole review. | Jeden krytyczny FAIL zatrzymuje całą ocenę. | TWARZ: AKCENT |
| L047 | Step six is paper trading. | Krok szósty: paper trading. | GRAFIKA: diagram — podświetlony etap „Paper trading” |
| L048 | The EA trades live prices on a demo account, with no real money at risk. | EA handluje na bieżących cenach na koncie demo, bez ryzykowania prawdziwych pieniędzy. | — |
| L049 | Real spreads, real fills, real trading hours. | Prawdziwe spready, prawdziwe realizacje zleceń, prawdziwe godziny handlu. | — |
| L050 | The market checks things a backtest never looked at. | Rynek sprawdza rzeczy, na które backtest nigdy nie patrzył. | TWARZ |
| L051 | Live trading is the last step. | Handel na żywo to ostatni krok. | GRAFIKA: diagram — podświetlony etap „Live” |
| L052 | Every update has to earn its way into production. | Każda zmiana musi zasłużyć na wejście do produkcji. | TWARZ |
| L053 | Any step can stop an idea. | Każdy krok może zatrzymać pomysł. | GRAFIKA: diagram — z każdego etapu strzałka w dół do pola „Log” |
| L054 | When that happens, the reason goes into a log. | Kiedy tak się dzieje, powód trafia do dziennika. | — |
| L055 | That log is the raw material for this channel. | Ten dziennik to surowiec dla tego kanału. | TWARZ |

## [3:33] Why it matters to you
<!-- Krok 2: zasada ogólna — błąd selekcji i przeuczenie dotyczą każdego, kto ogląda lub robi backtesty. -->
| ID | EN (mówione) | PL (napisy) | Na ekranie |
|---|---|---|---|
| L056 | Why should you care about my pipeline? | Dlaczego mój pipeline miałby Cię obchodzić? | TWARZ |
| L057 | Because most backtests you see online tell one side of the story. | Bo większość backtestów, które widzisz w sieci, opowiada jedną stronę historii. | — |
| L058 | Profitable backtests are easy to sell. | Zyskowne backtesty łatwo sprzedać. | — |
| L059 | I test whether they survive. | Ja sprawdzam, czy przetrwają. | TWARZ: AKCENT |
| L060 | Here's the problem. | Problem jest taki. | TWARZ |
| L061 | If you try enough ideas, one will look brilliant by chance. | Jeśli wypróbujesz dość pomysłów, jeden będzie wyglądał świetnie przez przypadek. | GRAFIKA: siatka wielu syntetycznych krzywych equity (bez osi i wartości), jedna wyróżniona |
| L062 | Then you see that one, and never the many that failed before it. | Potem widzisz ten jeden, a nigdy tych wielu, które odpadły przed nim. | — |
| L063 | This is called selection bias, and it fools experienced traders too. | To się nazywa błąd selekcji i nabiera nawet doświadczonych traderów. | — |
| L064 | The same thing happens inside one strategy. | To samo dzieje się wewnątrz jednej strategii. | TWARZ |
| L065 | Tune it long enough, and it learns the past by heart. | Strój ją wystarczająco długo, a nauczy się przeszłości na pamięć. | GRAFIKA: equity IS/OOS (syntetyczna, bez osi z wartościami, załamanie po OOS) |
| L066 | We call that overfitting. | Nazywamy to przeuczeniem, czyli overfittingiem. | — |
| L067 | The curve looks perfect on old data and breaks on new data. | Krzywa wygląda idealnie na starych danych i łamie się na nowych. | — |
| L068 | So a failed test is not wasted work. | Dlatego nieudany test to nie zmarnowana praca. | TWARZ |
| L069 | It tells you which assumption was wrong. | Mówi Ci, które założenie było błędne. | — |
| L070 | That's why I show failures with the same care as successes. | Dlatego pokazuję porażki z taką samą starannością jak sukcesy. | — |
| L071 | To be clear, a systematic approach does not promise more profit than manual trading. | Żeby było jasne: podejście systematyczne nie obiecuje większego zysku niż handel ręczny. | TWARZ |
| L072 | Its advantage is simpler: you can measure it, and you can test it. | Jego przewaga jest prostsza: możesz je zmierzyć i możesz je przetestować. | — |

## [4:37] How to check your own backtest
<!-- Krok 3: pytania, które widz zada każdemu backtestowi. CTA po kluczowym wniosku, na końcu sekcji. -->
| ID | EN (mówione) | PL (napisy) | Na ekranie |
|---|---|---|---|
| L073 | So how can you use this on your own strategies? | Jak więc wykorzystać to we własnych strategiach? | TWARZ |
| L074 | Before you trust any backtest, yours or someone else's, ask a few questions. | Zanim zaufasz jakiemukolwiek backtestowi, swojemu czy cudzemu, zadaj kilka pytań. | GRAFIKA: lista pytań kontrolnych (punkty wchodzą po kolei) |
| L075 | First: were real costs included? | Po pierwsze: czy uwzględniono prawdziwe koszty? | — |
| L076 | Spread, commission and slippage can turn a rising curve into a flat one. | Spread, prowizja i poślizg potrafią zamienić rosnącą krzywą w płaską. | — |
| L077 | Second: was any data kept away from the building process? | Po drugie: czy jakieś dane trzymano z dala od budowy strategii? | — |
| L078 | If every candle was used for tuning, the result is a memory test. | Jeśli każdą świecę wykorzystano do strojenia, wynik jest testem pamięci. | — |
| L079 | Third: how many versions were tried before this one? | Po trzecie: ile wersji wypróbowano przed tą? | — |
| L080 | Many versions of one idea are still one idea, tested many times. | Wiele wersji jednego pomysłu to wciąż jeden pomysł, testowany wiele razy. | — |
| L081 | Fourth: does the result hold when the settings change a little? | Po czwarte: czy wynik się utrzymuje, gdy ustawienia trochę się zmienią? | — |
| L082 | If a small change kills it, the result was probably luck. | Jeśli mała zmiana go zabija, wynik był prawdopodobnie szczęściem. | TWARZ: AKCENT |
| L083 | You don't need a big pipeline to ask these questions. | Nie potrzebujesz dużego pipeline'u, żeby zadać te pytania. | TWARZ |
| L084 | The MetaTrader tester and some patience are enough to start. | Tester MetaTradera i trochę cierpliwości wystarczą na początek. | EKRAN: MT5 Strategy Tester, Settings z rozwiniętą listą „Modeling” (nazwa EA zasłonięta, bez wyników) |
| L085 | If this kind of testing is useful, subscribe. | Jeśli takie testy są dla Ciebie wartościowe, zasubskrybuj. | BELKA: subscribe |
| L086 | Every month I publish what survived and what didn't. | Co miesiąc publikuję, co przetrwało, a co nie. | TWARZ |
| L087 | And a like helps the video reach other systematic traders. | A łapka w górę pomaga dotrzeć do innych traderów systematycznych. | TWARZ |

## [5:41] Channel rules and today's verdict
<!-- Krok 4: werdykt bez liczb — wprost mówimy, dlaczego ich nie ma. -->
| ID | EN (mówione) | PL (napisy) | Na ekranie |
|---|---|---|---|
| L088 | Now, the rules of this channel. | A teraz zasady tego kanału. | GRAFIKA: plansza „Channel rules” (punkty wchodzą po kolei) |
| L089 | I will never tell you that a strategy makes a certain profit. | Nigdy nie powiem Ci, że strategia daje określony zysk. | — |
| L090 | Every result comes with its costs, its test period, and its verdict. | Każdy wynik pokazuję razem z kosztami, okresem testu i werdyktem. | — |
| L091 | Failures get published, together with the reason they failed. | Porażki są publikowane razem z powodem, dla którego odpadły. | — |
| L092 | Strategies that pass are shown as summary numbers, not as recipes. | Strategie, które przechodzą, pokazuję jako zbiorcze liczby, a nie jako przepisy. | — |
| L093 | And every number comes from my own records, never from a made-up example. | A każda liczba pochodzi z moich zapisów, nigdy z wymyślonego przykładu. | — |
| L094 | That's why this video has no numbers at all. | Dlatego w tym filmie nie ma żadnych liczb. | TWARZ: AKCENT |
| L095 | My research log isn't public yet, and I won't quote numbers you can't check. | Mój dziennik badań nie jest jeszcze publiczny, a nie będę podawać liczb, których nie możesz sprawdzić. | TWARZ |
| L096 | So the verdict for today is simple. | Więc werdykt na dziś jest prosty. | TWARZ |
| L097 | The pipeline is built. | Pipeline jest zbudowany. | GRAFIKA: diagram pipeline'u — pełny, wszystkie etapy aktywne |
| L098 | Now it has to prove itself in public. | Teraz musi się sprawdzić publicznie. | TWARZ |

## [6:29] Disclaimer & next
| ID | EN (mówione) | PL (napisy) | Na ekranie |
|---|---|---|---|
| L099 | Whenever you see a test result on this channel, remember this. | Za każdym razem, gdy zobaczysz wynik testu na tym kanale, pamiętaj o tym. | TWARZ |
| L100 | Historical results, not investment advice. Past performance does not guarantee future results. | Wyniki historyczne, nie porada inwestycyjna. Wyniki z przeszłości nie gwarantują przyszłych. | TWARZ (+ tekst zastrzeżenia na dole kadru) |
| L101 | My free MetaTrader tools are on my mql5.com profile. | Moje darmowe narzędzia do MetaTradera są na moim profilu mql5.com. | EKRAN: profil mql5.com, lista publikacji w Code Base (zasłonięte sekcje Freelance, Market, Signals) |
| L102 | The link is in the description. | Link jest w opisie. | — |
| L103 | Subscribe for the next step. | Zasubskrybuj, żeby zobaczyć kolejny krok. | PLANSZA KOŃCOWA |
| L104 | And this video shows why a profitable backtest proves almost nothing. | A w tym filmie pokazuję, dlaczego zyskowny backtest prawie niczego nie dowodzi. | PLANSZA KOŃCOWA |

---

## Rozdziały (do opisu)
Czasy szacowane z liczby słów (~145 słów/min); po nagraniu podmienić na rzeczywiste.

| Czas | Rozdział (EN) | Pierwsze zdanie |
|---|---|---|
| 0:00 | Why I publish failures | L001 |
| 0:12 | Who I am | L004 |
| 0:53 | The pipeline: from paper to live | L013 |
| 3:33 | Why it matters to you | L056 |
| 4:37 | How to check your own backtest | L073 |
| 5:41 | Channel rules and today's verdict | L088 |
| 6:29 | Disclaimer and what's next | L099 |

## Trudne słowa (do próby czytania)
| Słowo / fraza | Wymowa / zamiennik |
|---|---|
| hypothesis (L018, L019, L022) | hai-PO-the-sis; akcent na „PO” |
| research (L008, L016, L095) | ri-SERCZ (akcent na drugą sylabę) |
| pipeline (L013, L014, L083, L097) | PAJP-lajn |
| Expert Advisor (L022, L023) | EKS-pert ad-WAJ-zer |
| MetaTrader five (L027) | ME-ta-trej-der fajw |
| MQL5 (L006) | em-kju-el-fajw |
| mql5.com (L101) | em-kju-el-fajw dot kom |
| slippage (L039, L076) | SLI-pydż |
| out-of-sample (L042) | aut-ow-SAM-pel |
| overfitting (L066) | OŁ-wer-fi-ting |
| selection bias (L063) | se-LEK-szyn BAJ-es |
| whether (L059) | ŁE-der (jak „weather”) |
| assumption (L069) | e-SAMP-szyn |
| conditional (L045) | kon-DI-szy-nal |
| commission (L076) | ko-MI-szyn |
| brilliant (L061) | BRI-lient; zamiennik: „great” |
| stress-test (L007) | STRES-test; zamiennik: „test hard” |
| earn its way into production (L052) | rytm: ERN-its-ŁEJ / in-tu-pro-DAK-szyn |
| Past performance does not guarantee (L100) | gje-ren-TI, akcent na końcu |

## Materiały do przygotowania przed nagraniem
- **Ujęcia twarzy (kamera, poziomo):** hook L001–L003; przedstawienie L004–L012; przerywniki w diagramie (L020, L026,
  L030, L035, L046, L050, L052, L055); cała sekcja „Why it matters” poza grafikami; CTA L083–L087; werdykt L094–L098;
  zastrzeżenie L099–L100. Kadr naprzemienny (reguła montażu 4) — nie trzeba nic robić przy nagraniu.
- **Zrzuty / nagrania ekranu (`EKRAN: …`) — wyłącznie konto demo:**
  - L006: MT5, czysty wykres jednego instrumentu, bez załadowanego EA. **Zasłonić / ukryć:** okno Nawigatora
    (lista Expert Advisors z nazwami), numer konta i nazwę serwera w tytule okna, Toolbox (Trade/History/Journal).
  - L027: MT5 Strategy Tester, zakładka **Settings**. **Zasłonić:** pole „Expert” (nazwa EA), pole „Inputs”
    (nie otwierać), zakładki Backtest/Graph/Results/Journal — nie klikać. Bez daty i deposit, jeśli zdradzają test.
  - L084: ten sam Tester, rozwinięta lista **„Modeling”** (np. „Every tick based on real ticks”) i pole „Delays”.
    Te same zasłonięcia co w L027; żadnych wyników.
  - L101: profil mql5.com, lista darmowych publikacji w Code Base. **Zasłonić:** sekcje Freelance (liczba prac,
    opinie), Market, Signals, saldo/konto, wiadomości. Bez liczb pobrań, jeśli są widoczne.
- **Grafiki (`GRAFIKA: …`):**
  - Diagram pipeline'u: Research → Code (EA generator) → MT5 backtest → Python backtest → Validation gates →
    Paper trading → Live, plus pole „Log” pod spodem. Wersje: wszystko wyszarzone (L013), kolejne podświetlenia
    etapów (L016, L021, L031, L036, L047, L051; L027 to zrzut MT5 zamiast podświetlenia), strzałki „stop” z każdego
    etapu do „Log” (L053), pełny aktywny diagram (L097). Bez nazw strategii, bez treści generatora.
  - Trzy etykiety PASS / CONDITIONAL / FAIL (L045), kolory: zieleń / bursztyn / czerwień.
  - Siatka wielu syntetycznych krzywych equity, jedna wyróżniona (L061) — dekoracja, bez osi i wartości.
  - Equity IS/OOS syntetyczna z załamaniem po OOS (L065) — bez osi i wartości.
  - Lista pytań kontrolnych (L074): costs included? / data kept away? / how many versions? / stable when settings change?
  - Plansza „Channel rules” (L088): no profit promises / costs, period, verdict / failures published / survivors as
    summaries / numbers from records.
  - Belki: `imie` (L004), `subscribe` (L085), tekst zastrzeżenia (L100), plansza końcowa (L103–L104) z linkiem
    do filmu #2 („Why a profitable backtest proves almost nothing”) — jeśli #2 nie jest jeszcze opublikowany,
    podmienić L104 na playlistę albo przeformułować.

## Checklista przed nagraniem
- [x] Brak zakazanych słów i języka sprzedaży o sobie (§7 strategii). „easy to sell” (L058) dotyczy innych.
- [x] Żadnych reguł/parametrów strategii przeznaczonych do sprzedaży.
- [x] Liczby z Ledgera / karty, nie ilustracyjne — film nie zawiera żadnych liczb.
- [x] Embargo (`publish_after`) — brak karty źródłowej, embargo nie dotyczy.
- [x] Każde zdanie EN ≤ 15 słów (poza zastrzeżeniem); trudne słowa przejrzane.
- [x] Grafiki: najwyżej jedna na myśl (one idea, one graphic).
- [x] Bez QuantInvest i quantinvest.co; CTA: subskrypcja + profil mql5.com.
- [ ] Film #2 opublikowany przed tym filmem albo L104 przeformułowane (plansza końcowa).

## Shorts (3–5 z tego filmu — zakresy ID)
1. L001–L003 + L056–L063: „Most channels show what worked” → błąd selekcji.
2. L064–L070: przeuczenie — krzywa idealna na starych danych, łamie się na nowych.
3. L074–L082: cztery pytania do każdego backtestu (najmocniejszy kandydat).
4. L088–L095: zasady kanału i dlaczego w tym filmie nie ma liczb.
5. L036–L046: bramki walidacji i werdykt PASS / CONDITIONAL / FAIL.
