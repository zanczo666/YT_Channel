# SpreadMonitorScalpers
Wersja: 1.32 (2026-09-15)
Link: https://www.mql5.com/en/code/76557
Problem: Scalper nie widzi, kiedy spread puchnie (rollover, newsy, otwarcie sesji), więc dobre wejście zamienia się w stratę, zanim świeca się uformuje.
Dla kogo: scalper i daytrader (początkujący do zaawansowanego); programista MQL5 — zapis historii do pliku i dopasowanie po czasie bara.
Zasada ogólna: Koszt transakcji jest częścią strategii — przy krótkich celach spread potrafi zjeść cały zysk, więc mierz go zanim wejdziesz, a nie po fakcie.
Hook (EN): Your scalping strategy might be fine — it's the spread you never see that's eating your profits.
Demo (60 s):
1. Wykres EURUSD M1 na demo. Podłącz wskaźnik — pod świecami otwiera się podokno z histogramem spreadu, czerwoną przerywaną linią progu i panelem statystyk.
2. Pokaż panel: Spread, Avg (100), Max, Min, Cost/trade (= spread × 2, koszt w obie strony).
3. Poczekaj na kilka ticków — ostatni słupek zmienia się, starsze stoją w miejscu, skala osi nie „oddycha”.
4. Obniż `Alert threshold (pips)` poniżej bieżącego spreadu — pojawia się alert; kolejny dopiero po cooldownie, nie co tick.
5. Przełącz M1 → M5 → z powrotem M1 — wcześniej zapisane słupki wracają.
6. Zmień symbol na XAUUSD — osobna historia, wartości „pips” znacznie wyższe; podnieś próg pod ten instrument.
Przed/po: Bez narzędzia: spread widać tylko jako jedną liczbę w Market Watch albo linię Ask na wykresie, bez historii i bez porównania ze średnią — skoki spreadu widać dopiero w wyniku transakcji. Z narzędziem: historia spreadu bar po barze, średnia/maksimum/minimum i alert, zanim klikniesz.
Haczyki:
- MT5 nie trzyma historii spreadu tick po ticku — histogram zbiera dane od chwili podłączenia, wcześniejsze bary są puste. To ograniczenie platformy, nie błąd.
- Historia jest zapisywana do pliku `MQL5\Files\SMS_hist_<symbol>_<timeframe>.bin` (osobno dla każdej pary symbol + timeframe); `InpPersistHistory=false` wyłącza zapis.
- „Pips” liczone wg liczby cyfr: na parach 5/3-cyfrowych 1 pip = 10 punktów, na symbolach o innej liczbie cyfr (np. złoto 2 cyfry) 1 „pip” = 1 punkt — domyślny próg 2.0 na złocie będzie alarmował bez przerwy.
- Skala histogramu jest stała: domyślnie 0 → 4 × próg; jeśli spread regularnie ją przebija, ustaw `Histogram scale ceiling (pips)` ręcznie.
- Spread 0 (brak kwotowania, rynek zamknięty) jest pomijany — dlatego Min nie przykleja się do 0.0 (poprawka v1.32).
- Alerty push wymagają skonfigurowanego MetaQuotes ID w terminalu; domyślnie wyłączone.
Pokazać na ekranie:
- Podokno z histogramem, linią progu i panelem statystyk.
- Okno inputów (próg, skala, zapis historii, alerty).
- Kod: `SpreadMonitorScalpers.mq5`, funkcje `SaveHistory()` / `LoadHistory()` — zapis per symbol+timeframe i dopasowanie punktów po czasie bara, nie po indeksie.
- Opcjonalnie `CurrentSpreadPips()` — przeliczenie punktów na pipsy.
Nie pokazywać:
- Numeru konta, nazwy brokera i serwera, realnego konta.
- Bloku z linkami do innych produktów z `opis.md` (w tym płatnych) ani profilu jako „oferty”.
- Niczego z prac wykonywanych dla innych osób (kod, wykresy, okna MetaEditora z innymi projektami).
