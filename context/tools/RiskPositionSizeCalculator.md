# RiskPositionSizeCalculator
Wersja: 1.11 (2026-08-04)
Link: https://www.mql5.com/en/code/75686
Problem: Przy stałym locie strata w pieniądzach zmienia się z każdą zmianą odległości stopa, a trader widzi ją dopiero po otwarciu pozycji.
Dla kogo: początkujący i średniozaawansowany (trader ręczny); programista MQL5 — fragment z `OrderCalcProfit()`.
Zasada ogólna: Wielkość pozycji jest ważniejsza niż wejście — najpierw decydujesz, ile możesz stracić, a lot wynika ze stopa, nie odwrotnie.
Hook (EN): Same stop, same pair — but a 1-lot trade can cost you ten times more than you think; here's how to size every trade from risk instead.
Demo (60 s):
1. Wykres EURUSD H1 na koncie demo, ciemny motyw. Przeciągnij EA na wykres — pojawiają się linie Entry (ciągła), Stop (ciągła) i Target (kropkowana) oraz panel w rogu.
2. W inputach pokaż `Risk per trade (%)` = 1 i `Risk base` = Balance.
3. Przeciągnij linię Stop bliżej wejścia — lot w panelu rośnie, kwota ryzyka w walucie konta stoi w miejscu.
4. Odsuń Stop dalej — lot maleje, ryzyko nadal to samo. To jest sedno filmu.
5. Przesuń Stop powyżej wejścia — kierunek przełącza się sam na sprzedaż.
6. Ustaw `Reward:risk` = 2 — linia Target przeskakuje na 2R i pokazuje kwotę celu.
7. Zmień symbol na XAUUSD lub parę krzyżową (np. EURJPY) — liczby nadal poprawne w walucie konta.
8. Ustaw bardzo daleki stop na małym koncie — panel pokazuje „Below broker minimum …” zamiast `0.00`.
Przed/po: Bez narzędzia: stały lot (np. 0.10) na każdą transakcję albo liczenie w głowie „punkty × wartość punktu”, które na parach krzyżowych, złocie i CFD po cichu się rozjeżdża; ryzyko w pieniądzach widać dopiero w otwartej pozycji. Z narzędziem: ta sama kwota ryzyka na każdej transakcji, widoczna przed wejściem.
Haczyki:
- Lot jest zawsze zaokrąglany W DÓŁ do kroku brokera — realne ryzyko bywa minimalnie niższe niż ustawione procenty; to celowe, nie błąd.
- „Below broker minimum” oznacza, że przy tym stopie nawet minimalny lot przekracza zadeklarowane ryzyko — panel podaje, ile wtedy ryzykujesz; trzeba skrócić stop albo zaakceptować wyższe ryzyko.
- `Risk base`: Balance ignoruje otwarte pozycje, Equity je uwzględnia, Free margin jest najbardziej konserwatywne — wyniki się różnią, gdy masz otwarte pozycje.
- Stop po złej stronie wejścia przy wymuszonym kierunku daje komunikat „Stop loss is on the wrong side of the entry”.
- To Expert, nie wskaźnik — na wykresie, na którym już działa inny EA, się nie podłączy.
- Narzędzie niczego nie otwiera — lot trzeba przepisać ręcznie do okna zlecenia.
Pokazać na ekranie:
- Panel z wierszami Position size / Risk / Margin needed / Target oraz przeciągane linie.
- Okno inputów (grupy Risk, Levels, Appearance).
- Kod: `RiskPositionSizeCalculator.mq5`, funkcja `ComputeSize()` — wycena stopa przez `OrderCalcProfit()` dla 1 lota i zaokrąglenie `MathFloor` w dół do kroku wolumenu.
Nie pokazywać:
- Numeru konta, nazwy brokera i serwera, salda innego niż konto demo (wiersz konta w panelu pokazuje saldo/equity — tylko demo).
- Prawdziwego konta i otwartych realnych pozycji.
- Bloku „Need a custom version…” z `opis.md` ani żadnych innych płatnych produktów.
- Niczego z prac wykonywanych dla innych osób (kod, wykresy, okna MetaEditora z innymi projektami).
