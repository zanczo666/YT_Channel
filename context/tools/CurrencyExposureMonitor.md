# CurrencyExposureMonitor
Wersja: 1.00 (2026-10-27)
Link: https://www.mql5.com/en/code/78944
Problem: Trader trzyma kilka pozycji na różnych parach i nie widzi, że razem to jeden duży zakład na jedną walutę; terminal pokazuje listę transakcji, nie ekspozycję walutową ani faktyczną dźwignię konta.
Dla kogo: trader trzymający kilka pozycji naraz (ręcznie albo kilkoma EA), osoby przechodzące z MT4 (tam był wbudowany iExposure); programista MQL5 — rozbijanie pozycji na nogi walutowe i przeliczanie na walutę konta.
Zasada ogólna: Ryzyko siedzi w walutach, nie w symbolach — zanim dołożysz transakcję, sprawdź, na czym konto naprawdę stoi i ile kosztowałby zwykły ruch 1%.
Hook (EN): Four different trades — or one big bet against the dollar? Your position list won't tell you.
Demo (60 s):
1. Konto demo, otwarte: EURUSD buy, GBPUSD buy, USDJPY sell, XAUUSD buy. Pokaż listę pozycji — wygląda na cztery różne transakcje.
2. Podłącz wskaźnik do dowolnego wykresu — czerwony słupek USD na ~99% ekspozycji z (!).
3. Pokaż linię „Effective leverage” (np. 12.9 : 1 obok „broker 1:100”) i sekcję „If one rises 1.0%”: USD +1% = −12,8% equity.
4. Najedź na wiersz USD — podpowiedź pokazuje, z których pozycji się składa.
5. Zamknij GBPUSD, USDJPY, XAUUSD, otwórz USDCHF buy — USD prawie zero, za to CHF short: ukryta pozycja EURCHF.
6. Zmień `Sensitivity: currency move, %` na 2 — kwoty wrażliwości się podwajają.
Przed/po: Bez narzędzia: lista transakcji po symbolach, łączny zysk/strata, margin — ale nie widać, ile konto stawia na każdą walutę ani jaka jest faktyczna dźwignia. Z narzędziem: słupki ekspozycji per waluta w walucie konta, efektywna dźwignia i skutek ruchu 1% od razu na wykresie.
Haczyki:
- Kurs przeliczenia waluty zysku jest brany z pary forex w Market Watch (waluta kwotowana albo bazowa, np. EUR przez EURUSD); gdy pary nie ma, awaryjnie wartość tiku brokera — dla CFD mniej dokładna, więc warto trzymać pary walut konta w Market Watch.
- Wartość tiku podawana przez brokera dla CFD bywa niezgodna z kontraktem (na MetaQuotes-Demo XAUUSD ma 1/10 realnej) — dlatego dla forex/CFD liczymy kontrakt × cena × kurs, a wartość tiku dla futures i awaryjnie.
- Indeksy, akcje i towary CFD (US500, DE40) są wierszem „aktywa”, nie walutą — ryzyko walutowe dotyczy tam tylko bieżącego P/L.
- Wrażliwość to przybliżenie liniowe; nie uwzględnia korelacji walut (EUR i GBP często idą razem), swapów ani prowizji.
- Zlecenia oczekujące nie są liczone (planowane w kolejnej wersji).
- Na ekranie ze skalowaniem panel rośnie razem z DPI — przy małym oknie zmniejsz `Panel font size`.
Pokazać na ekranie:
- Panel ze słupkami, dźwignią i wrażliwością w scenie „jeden zakład” i w scenie „ukryty EURCHF”.
- Okno inputów (filtr magic, procent wrażliwości, progi dźwigni i koncentracji).
- Kod: `CurrencyExposureMonitor.mq5`, funkcje `AddPosition()` (rozbicie na nogi), `PositionNotional()` i `CurrencyRate()` (przeliczenie na walutę konta).
Nie pokazywać:
- Numeru konta, nazwy brokera i serwera, realnego konta.
- Linków do innych produktów ani profilu jako „oferty”.
- Niczego z prac wykonywanych dla innych osób (kod, wykresy, okna MetaEditora z innymi projektami).
