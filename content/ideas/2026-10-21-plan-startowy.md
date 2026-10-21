# Plan startowy — pierwsze 10 filmów

_2026-10-21. Tytuły robocze EN. Liczby w nawiasach `N`/`K` uzupełniamy WYŁĄCZNIE z Ledgera / kart `context/factory/`._
_Wspólne dla wszystkich: napisy EN + PL, rozdziały `0:00`, disclaimer, CTA niesprzedażowe._

| # | Filar | Tytuł roboczy | Hak (pierwsze 15 s) | Co pokazać | Czego NIE pokazywać | Zależność |
|---|---|---|---|---|---|---|
| 1 | Intro | From research papers to live algorithms — and publishing every failure | „Most trading channels show you what worked. I'm going to show you what didn't — and why.” | Twarz; diagram pipeline'u (research → generator → MT5 → Python → walidacja); zasady kanału | Promptów, nazw strategii w sprzedaży, liczb przed Ledgerem | brak |
| 2 | Validation Gates | Why a profitable backtest proves almost nothing | „A backtest is a story about the past. Here's how to check if it's a true one.” | Lista bramek PASS/CONDITIONAL/FAIL; przykład szczytu parametru vs plateau | Wyników strategii na sprzedaż | brak |
| 3 | Paper vs Reality | (tytuł wg publikacji) | „This paper reports X. I ran the same idea with real costs.” | Publikacja, implementacja, wynik po kosztach i OOS, werdykt | Parametrów, jeśli strategia przeszła i idzie do sprzedaży | źródło publikacji w Ledgerze |
| 4 | The Funnel | N hypotheses in, K survived — month one of the factory | „Last month my pipeline tested N ideas. K survived. Here's where the rest died.” | Tabela lejka z karty `funnel/`, powody odrzutu, liczba prób | Szczegółów przetrwałych strategii (tylko agregaty) | pierwsza karta `funnel/` |
| 5 | Tools | A free position-size calculator for MT5 (and why sizing matters more than entries) | „Two traders, same entries, different results. The difference is position size.” | Narzędzie z Code Base, demo na koncie demo | Linków do płatnych produktów | karta `VIDEO.md` |
| 6 | Validation Gates | Spread +50%: the stress test most EAs fail | „Add a little more spread and watch what happens to the profit factor.” | Tabela stresu kosztów na strategii odrzuconej | Strategii na sprzedaż | wyniki stresu z fabryki |
| 7 | Strategy Graveyard | Graveyard #1: (QF-xxx) | „This strategy looked great. It died at gate N. Here's the autopsy.” | Pełna logika, wyniki per etap, powód odrzutu | Niczego bez `graveyard: approved` | karta `graveyard/` approved |
| 8 | Validation Gates | Same strategy, two backtest engines, different results | „Python said one thing. MetaTrader said another. Both were 'right'.” | Lekcja z parytetu PF (0/0) — przypadek brzegowy metryki | Kodu generatora i promptów | karta `lessons/` (parytet PF) |
| 9 | Paper vs Reality | (tytuł wg publikacji #2) | jak #3 | jak #3 | jak #3 | jak #3 |
| 10 | Validation Gates | How many variants did you really test? | „If you test enough ideas, one will look brilliant by chance.” | Limit wariantów na pomysł w fabryce, idea Deflated Sharpe | Parametrów strategii | karta `lessons/` (limit wariantów) |

## Kandydaci z historii fabryki (do potwierdzenia kartami `lessons/`)
- **Martwy warunek wykryty na bramce smoke** (0 wejść na danych syntetycznych) → *„The EA that never trades: catching dead conditions before backtesting”*.
- **Parytet PF przy 0/0** → film #8.
- **Limit wariantów jednego pomysłu** w Rank & Dedup → film #10.
- **Klasa krypto w silniku** (koszty, rollover 7 dni, weekendy) → *„Crypto never sleeps: what changes in your backtest”*.

## Zasady kolejności
- Filmy #1, #2 i #5 nie zależą od eksportu fabryki, więc można je robić od razu (#5 wymaga tylko karty `VIDEO.md`).
- Pozostałe czekają na karty w `context/factory/` i na minięcie embargo.
