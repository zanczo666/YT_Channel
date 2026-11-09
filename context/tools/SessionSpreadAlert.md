# SessionSpreadAlert
Wersja: 1.10 (2026-08-19)
Link: brak — w repo status `review` (`mql5/README.md`), adresu publikacji w CodeBase nie ma; uzupełnić po publikacji.
Problem: Trader nie wie, która płynność jest właśnie aktywna, i nie zauważa, że spread wokół otwarcia sesji albo rolloveru urósł kilkukrotnie.
Dla kogo: początkujący (trader ręczny, handel otwarć sesji); programista MQL5 — parsowanie godzin `HH:MM` i sprzątanie obiektów.
Zasada ogólna: Liczy się nie tylko gdzie wejść, ale kiedy — pora dnia i koszt wejścia decydują o wyniku tak samo jak sygnał.
Hook (EN): The London open can turn a dead range into a trend — and triple your spread in the same minute.
Demo (60 s):
1. Wykres EURUSD M5 na demo. Podłącz wskaźnik — na wykresie pojawiają się kropkowane pionowe linie otwarć sesji Sydney, Tokio, Londyn, Nowy Jork i panel spreadu w rogu.
2. Najedź kursorem na linię — tooltip pokazuje nazwę sesji.
3. W inputach pokaż cztery godziny `HH:MM` i wyjaśnij, że to czas serwera brokera; zmień jedną godzinę — linie się przerysowują.
4. Obniż `Spread threshold (pips)` poniżej bieżącego spreadu — wiersz spreadu w panelu robi się czerwony, pojawia się alert; kolejny dopiero po cooldownie.
5. Pokaż przykładowy alert otwarcia sesji z bieżącym spreadem (np. „London session open - spread: 1.2 pips”).
6. Usuń wskaźnik — wykres czysty, żadnych pozostałych linii.
Przed/po: Bez narzędzia: pilnowanie zegara i przeliczanie strefy czasowej brokera w głowie, spread widoczny tylko w Market Watch. Z narzędziem: otwarcia sesji zaznaczone na wykresie, spread na panelu i alert w chwili otwarcia lub przekroczenia progu.
Haczyki:
- Godziny sesji to czas SERWERA brokera, nie czas lokalny — domyślne wartości są oparte na UTC i u większości brokerów trzeba je przesunąć (także przy zmianie czasu letni/zimowy).
- Godzinę trzeba wpisać z dwukropkiem (`08:00`); zapis z kropką (`8.00`) albo spoza zakresu (`24:00`) jest odrzucany i linia tej sesji się nie narysuje.
- `Max session lines` (domyślnie 40) — starsze linie są kasowane; podnieś, jeśli chcesz dłuższą historię wizualną.
- „Pips” liczone wg liczby cyfr: na złocie (2 cyfry) 1 „pip” = 1 punkt, więc domyślny próg 2.0 będzie alarmował bez przerwy — ustaw próg pod instrument.
- Alert otwarcia sesji pojawia się raz na sesję, tylko gdy terminal działa w tej chwili; nie nadrabia przegapionych otwarć.
- Push wymaga skonfigurowanego MetaQuotes ID w terminalu; domyślnie wyłączony.
Pokazać na ekranie:
- Linie sesji z tooltipami i panel spreadu (normalny i czerwony po przekroczeniu progu).
- Okno inputów (godziny sesji, próg, cooldown, push).
- Kod: `SessionSpreadAlert.mq5`, funkcje `ParseTimeToMinutes()` (walidacja `HH:MM`) i `TrimSessionLines()` (limit obiektów na wykresie).
Nie pokazywać:
- Numeru konta, nazwy brokera i serwera, realnego konta.
- Bloku z linkami do innych produktów z `opis.md` (w tym płatnych).
- Niczego z prac wykonywanych dla innych osób (kod, wykresy, okna MetaEditora z innymi projektami).
- Do czasu publikacji: nie podawać linku ani nie mówić, że narzędzie jest w CodeBase.
