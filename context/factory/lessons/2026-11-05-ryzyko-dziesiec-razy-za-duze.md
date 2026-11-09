---
typ: lesson
data_zdarzenia: 2026-11-05
etap: 02_MT5_Backtest
publish_after: 2026-11-26
---
# Ryzyko 1,5% w kodzie, 15% na koncie: błąd, którego backtest w Pythonie nie zobaczy
## Co się wydarzyło
Strategia na złocie odpadła w szybkim teście Pythona, ale trafiła do losowej grupy kontrolnej, która mimo odrzucenia idzie dalej do testera MT5.
Tester pokazał stratę kapitału 87%, choć model Pythona miał 12,4%. Ustawione ryzyko wynosiło 1,5% na transakcję, a mediana straty 15,1% kapitału.
## Przyczyna
Wzór na wielkość pozycji brał wartość ticku ze specyfikacji symbolu, a na metalach była ona 10 razy za niska. Silnik Pythona nie liczy pozycji z kodu EA, więc nie ma jak tego wykryć.
Po przejściu na liczenie straty przez funkcję platformy ten sam EA zrobił te same 174 transakcje z medianą straty 1,46% i spadkiem kapitału 15,2%.
## Zasada ogólna
Dwie implementacje strategii mogą zgadzać się co do liczby transakcji i wciąż różnić się wielkością pozycji. Grupa kontrolna pokazuje usterki w miejscach, do których odrzucone strategie zwykle nie docierają.
## Jak wykryć u siebie
Podziel każdą stratę na stopie przez kapitał sprzed transakcji i porównaj z ustawionym ryzykiem. Mediana wyraźnie inna niż ustawienie oznacza błąd wielkości pozycji, nie zmienność rynku.
Sprawdzaj to na każdej klasie instrumentów osobno. Nie ufaj polu specyfikacji, jeśli platforma potrafi policzyć wynik transakcji sama.
## Liczby
- Ustawione ryzyko: 1,5%. Mediana straty w testerze: 15,1%, najgorsza 18,2% kapitału.
- Spadek kapitału: tester MT5 87,3%, model Pythona 12,4%.
- Transakcje: tester 174, Python 159. Profit factor: tester 1,04, Python 1,24.
- Na indeksie w tym samym tygodniu najgorsza transakcja to −1,03% przy ryzyku 1%, więc problem nie dotyczy wszystkich instrumentów.
## Można pokazać
- Histogram strat w procentach kapitału z linią ustawionego ryzyka.
- Krzywą kapitału z testera obok krzywej z Pythona.
## Nie pokazywać
- Promptów generatora, kodu EA i danych brokera.
