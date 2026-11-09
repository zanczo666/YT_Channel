---
typ: lesson
data_zdarzenia: 2026-10-13
etap: 01_EA_Generator
commit: 56f8315
publish_after: 2026-11-03
---
# Martwy warunek wejścia: strategia, która nigdy nie może otworzyć pozycji
## Co się wydarzyło
13.10 strategia breakoutowa z publikacji przeszła audyt i kompilację, po czym w backteście dała 0 transakcji.
Bramka smoke w generatorze (krótki przebieg na syntetycznych świecach) zgłosiła 0 wejść, ale tylko jako
ostrzeżenie, więc kod poszedł dalej. Od tego dnia bramka wymusza jedną poprawkę kodu po wykryciu 0 wejść.
Do 22.10 wykryła tak 5 przypadków — automatyczna poprawka przez LLM naprawiła 0 z 5.
## Przyczyna
Dwa błędy w kodzie: pasmo liczone wokół bieżącego zamknięcia (górna granica = close + odchylenie), więc warunek
„close powyżej górnej granicy” jest matematycznie niemożliwy, a warunki łączył AND. Drugi: opis „VWAP + średnia”
odczytany jako suma dwóch cen (≈ 2× cena) zamiast dwóch osobnych filtrów. Poprawka nie działała, bo model
dostawał tylko informację „0 wejść” — nie wiedział, który z kilku warunków jest zawsze fałszywy.
## Zasada ogólna
Zero transakcji to prawie zawsze błąd implementacji, nie „ostrożna strategia”. Wykrycie objawu jest łatwe;
naprawa wymaga wskazania, który człon warunku nigdy nie jest prawdziwy.
## Jak wykryć u siebie
Uruchom strategię na losowym spacerze cen (kilka tysięcy świec) i policz, ile razy prawdziwy jest KAŻDY człon
warunku wejścia osobno. Człon z 0 trafień na losowych danych = martwy kod. Ostrzeżenie: liczba wejść 0 albo
sygnał na > 15% świec (drugi skrajny przypadek — zbyt gęste sygnały).
## Liczby
- Dane syntetyczne: 24 768 świec, 0 wejść.
- Przypadki wykryte przez bramkę (13–22.10): 5; naprawione automatycznie: 0/5.
- Typowa strategia na tych samych danych: sygnał na 0–4% świec.
## Można pokazać
- Schemat bramki smoke: dane syntetyczne → liczba wejść → poprawka / przepuszczenie.
- Pseudokod błędu `close > close + σ` (ilustracja, nie kod strategii).
- Licznik 5 wykrytych / 0 naprawionych.
## Nie pokazywać
- Promptu generatora ani promptu poprawki.
- Wygenerowanego kodu strategii i ścieżek w magazynie plików.
