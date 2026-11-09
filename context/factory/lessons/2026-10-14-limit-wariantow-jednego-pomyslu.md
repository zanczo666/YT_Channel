---
typ: lesson
data_zdarzenia: 2026-10-14
etap: 00_Deep_Research
commit: 8db1a00
publish_after: 2026-11-04
---
# Pięć „różnych” strategii, jeden pomysł: deduplikacja po nazwie nie działa
## Co się wydarzyło
W nocy 14.10 research znalazł 5 strategii z różnych źródeł i pod różnymi nazwami. Wszystkie były wariantem
tej samej idei (przełączanie reżimu wg wykładnika Hursta) na tym samym rynku i interwale. Każda poszła do
generatora kodu; jedna odpadła już tam, cztery odrzucił backtest. Koszt: 5 przebiegów generatora za jedną hipotezę.
## Przyczyna
Deduplikacja porównywała tylko znormalizowaną nazwę strategii. Autorzy nazywają ten sam mechanizm różnie,
więc filtr niczego nie łapał. Poprawka: klucz pomysłu = styl strategii + rynek + interwał i limit 2 wariantów
jednego pomysłu na noc (także między partiami wyszukiwania).
## Zasada ogólna
Pięć wariantów jednego pomysłu to nie pięć niezależnych prób — to jedna próba wykonana pięć razy, która
przy okazji zwiększa szansę na przypadkowy „sukces” (problem wielokrotnego testowania). Liczyć trzeba pomysły, nie nazwy.
## Jak wykryć u siebie
Pogrupuj testowane strategie po (mechanizm, rynek, interwał) i policz warianty w grupie. Grupa z wieloma
wariantami = albo przepalasz budżet, albo nieświadomie dopasowujesz parametry. Licz wszystkie warianty w statystyce (np. deflowany Sharpe).
## Liczby
- Warianty jednego pomysłu w jednej nocy: 5; odpadły w generatorze: 1; w backteście: 4; przeszły: 0.
- Limit po poprawce: 2 warianty pomysłu na noc.
## Można pokazać
- Lista 5 nazw obok jednego klucza pomysłu (bez reguł strategii).
- Schemat: nazwa → klucz pomysłu → limit.
## Nie pokazywać
- Promptów researchu i ekstrakcji.
- Pełnych opisów strategii z JSON-ów.
