---
typ: lesson
data_zdarzenia: 2026-11-09
etap: 03_Python_Backtest
publish_after: 2026-11-30
---
# Profit factor 11 z jednej pozycji trzymanej prawie 11 lat
## Co się wydarzyło
Automatyczny research znalazł znaną anomalię kalendarzową na indeksie US500. Publiczny opis podawał moment wejścia, ale nie podawał, kiedy wyjść.
System wygenerował kod i policzył backtest: profit factor 11,09 i zwrot +109,8% przy spadku kapitału 11,2%. Bramka odrzuciła wynik, bo w próbie było tylko 8 transakcji.
## Przyczyna
Bez reguły wyjścia pozycję mógł zamknąć tylko stop-loss. Siedem transakcji skończyło się stratą w 2012 roku, a ósma trwała od stycznia 2013 do listopada 2023, czyli do końca danych. Prawie cały wynik to wzrost rynku w tej jednej pozycji, a nie badana anomalia.
Filtr wejściowy szukał dokładnych słów oznaczających brak stop-lossa i nie rozpoznał znacznika „brakujące dane”, a obecności reguły wyjścia w ogóle nie sprawdzał.
## Zasada ogólna
Metryka zbiorcza nie mówi, co właściwie zostało przetestowane. Strategia bez zdefiniowanego wyjścia to nie jest niekompletna wersja pomysłu, tylko inny test: kup i trzymaj z przypadkowym momentem startu.
## Jak wykryć u siebie
Obejrzyj log transakcji, a nie tylko podsumowanie. Sygnały ostrzegawcze to średni czas w pozycji wielokrotnie dłuższy od założonego, ostatnia transakcja zamknięta przez koniec danych oraz zysk skupiony w jednej pozycji.
Przed backtestem wymagaj jawnej reguły wyjścia i odrzucaj specyfikacje, w których jest puste pole.
## Liczby
- Profit factor: 11,09. Zwrot: +109,8%. Spadek kapitału: 11,2%.
- Transakcje w próbie: 8, w tym 1 zyskowna (win rate 12,5%).
- Najdłuższa pozycja: 2802 bary dzienne, zamknięta przez koniec danych.
## Można pokazać
- Log ośmiu transakcji z czasem trwania.
- Log bramki z powodami odrzucenia.
## Nie pokazywać
- Promptów generatora, JSON-a strategii i kodu EA.
