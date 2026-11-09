---
typ: lesson
data_zdarzenia: 2026-10-14
etap: 02_MT5_Backtest
commit: 6aa8348
publish_after: 2026-11-04
---
# 0 / 0 ≠ niezgodność: jak dzielenie przez zero odrzuciło idealnie zgodny EA
## Co się wydarzyło
14.10 bramka parytetu (porównanie EA w MetaTraderze z modelem w Pythonie) odrzuciła strategię z powodu
niezgodnego Profit Factor. Tymczasem obie implementacje dały dokładnie to samo: 8 transakcji, wszystkie stratne.
## Przyczyna
Profit Factor = zysk brutto / strata brutto. Bez ani jednej zyskownej transakcji PF = 0 po obu stronach,
a bramka porównywała iloraz PF_MT5 / PF_Python = 0 / 0. Wynik nieokreślony był traktowany jak „poza zakresem
[0,8; 1,25]” → odrzucenie za brak parytetu. Poprawka: gdy oba PF = 0, parytet ocenia się po znaku średniej
transakcji, a iloraz PF zapisuje jako brak wartości.
## Zasada ogólna
Każda metryka będąca ilorazem (PF, Sharpe, Recovery) ma przypadki brzegowe: 0 / 0, x / 0, mała próbka.
Bramka, która ich nie obsługuje jawnie, podejmuje decyzję za pomocą przypadku, nie danych.
## Jak wykryć u siebie
Przepuść przez swoją bramkę trzy sztuczne logi transakcji: same zyski, same straty, zero transakcji. Jeśli
któryś daje NaN / inf albo decyzję, której nie umiesz uzasadnić — bramka ma dziurę.
## Liczby
- Transakcje: MT5 8, Python 8; zyskowne 0 / 0; PF 0 / 0; WR 0% / 0%.
- Testy bramki po poprawce: 15 (3 nowe dla przypadków brzegowych).
## Można pokazać
- Tabelka porównania MT5 vs Python (liczba transakcji, WR, PF) dla tego przypadku.
- Wzór PF i trzy przypadki brzegowe.
## Nie pokazywać
- Kodu i parametrów strategii (odrzucona, ale nie ma statusu graveyard).
