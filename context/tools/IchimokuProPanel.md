# IchimokuProPanel
Wersja: 2.10 (2026-08-19)
Link: brak — w repo status `review`, planowana platforma to Market (Free), nie CodeBase (`mql5/README.md`); uzupełnić po publikacji.
Problem: Wbudowany Ichimoku na ciemnym wykresie to plątanina pięciu linii z chmurą w kolorach słabo widocznych na ciemnym tle i bez wartości na wykresie, więc trend trzeba odczytywać zamiast go widzieć.
Dla kogo: początkujący i średniozaawansowany (trader używający Ichimoku); programista MQL5 — `DRAW_FILLING` z kanałem alfa i przesunięcia plotów.
Zasada ogólna: Czytelność wykresu to część analizy — wskaźnik, którego nie odczytasz w sekundę, i tak zignorujesz w chwili decyzji.
Hook (EN): Ichimoku isn't confusing — the default way MetaTrader draws it is.
Demo (60 s):
1. Wykres EURUSD H1, ciemny motyw, obok wbudowany Ichimoku (dla porównania, potem go usuń).
2. Podłącz IchimokuProPanel — pięć linii, półprzezroczysta chmura Kumo i panel wartości z prawej.
3. Przewiń do miejsca, gdzie Span A przecina Span B — chmura zmienia kolor z zielonego na czerwony.
4. Pokaż panel: Tenkan, Kijun, Span A, Span B, Chikou, Kumo top, Kumo bottom.
5. W inputach zmień `Kumo opacity` z 120 na 60 i na 200 — różnica w przezroczystości chmury.
6. Zmień symbol na USDJPY lub XAUUSD — panel sam dopasowuje liczbę miejsc po przecinku.
Przed/po: Bez narzędzia: wbudowany Ichimoku rysuje chmurę bez regulacji przezroczystości, w kolorach, które na ciemnym tle się zlewają, a wartości linii trzeba wyciągać z okna danych. Z narzędziem: chmura wypełniona kolorem trendu, kolory dobrane pod ciemny wykres i wartości na panelu.
Haczyki:
- Przesunięcia są inputami: `Senkou shift` = 26 (do przodu), `Chikou shift` = −26 (do tyłu). Zmiana znaku Chikou na dodatni przesuwa go w przyszłość — to częsty błąd przy „dostrajaniu”.
- Okresy 9/26/52 to wartości klasyczne; na rynkach otwartych 24/5 część traderów stosuje inne — panel liczy zawsze wg ustawionych okresów.
- `Kumo opacity` 0 = chmura niewidoczna, 255 = pełne krycie zasłaniające świece; rozsądny zakres to ok. 80–160.
- Panel wartości używa obiektów z prefiksem `IPP_LBL_` — skrypty „usuń wszystkie obiekty” go skasują; wskaźnik odtworzy go przy następnym ticku.
- Kolory domyślne są dobrane pod ciemny motyw — na jasnym tle srebrny Chikou i etykiety są słabo widoczne.
- To przerysowanie wizualne standardowego Ichimoku (`iIchimoku`), nie inna metoda liczenia — wartości są takie same jak we wbudowanym wskaźniku.
Pokazać na ekranie:
- Porównanie obok siebie: wbudowany Ichimoku i IchimokuProPanel na tym samym wykresie.
- Moment zmiany koloru chmury i panel wartości.
- Kod: `IchimokuProPanel.mq5`, funkcja `OnInit()` — `ColorToARGB()` z kanałem alfa dla dwóch kolorów `DRAW_FILLING` i `PLOT_SHIFT` dla Span A/B i Chikou.
Nie pokazywać:
- Numeru konta, nazwy brokera i serwera, realnego konta.
- Bloku z linkami do innych produktów z `opis.md` (w tym płatnych).
- Niczego z prac wykonywanych dla innych osób (kod, wykresy, okna MetaEditora z innymi projektami).
- Do czasu publikacji: nie podawać linku ani nie mówić, że narzędzie jest w CodeBase lub w Market.
