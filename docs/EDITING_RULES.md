# Reguły montażu i scenariusza (rosną z każdym filmem)

> Pętla nauki (wniosek z analizy 2026-10-29): po każdej wersji montażu uwagi trafiają do
> `content/notes/<slug>-cutN.md` (z sekundami). Dla każdej uwagi Claude wskazuje regułę, która by jej zapobiegła,
> i dopisuje ją tutaj. Czytają to agenci `yt-scriptwriter` i `yt-producer` (oraz przyszły montaż).

## Scenariusz
1. Jedno zdanie EN = jeden wiersz z ID, ≤ 15 słów.
2. One idea, one graphic — grafika najwyżej co kilka zdań.
3. CTA dopiero po kluczowym wniosku, nigdy w pierwszych 30 s.

## Nagrywanie (z pierwszego nagrania próbnego, 2026-11-02)
1. **Pauza między zdaniami jest częścią pracy, nie przerwą.** Pół sekundy ciszy wystarczy. Dwa zdania
   powiedziane bez oddechu zlewają się w jedno ujęcie i dopasowanie musi wybrać jedno z nich.
2. **Po pomyłce powtarzaj całe zdanie od początku**, nie od słowa, na którym się potknąłeś — inaczej
   w nagraniu nie ma ani jednego pełnego ujęcia tego zdania.
3. **Nagrywaj poziomo.** Pierwsze nagranie próbne przyszło pionowe (1080×1920) i cały montaż policzył się
   dla wąskiego kadru. Pionowy kadr zostaw na shorts (C13). C1 od tej pory głośno o tym ostrzega.
4. **Mów bliżej mikrofonu.** Nagranie z odległości wyszło na −30 LUFS; dźwięk da się podnieść, ale razem
   z poziomem rośnie szum pomieszczenia, a kompresja musi pracować mocniej.

## Montaż
1. Z kilku ujęć tego samego zdania zostaje ostatnie czyste.
2. Pauzy dłuższe niż ~0,6 s skracane; **krótszych nie ruszamy** — oddech między zdaniami jest treścią,
   nie pustym miejscem (uwaga „sztywny montaż”, `content/notes/_test-nagranie-cut1.md`).
3. Grafika nie zasłania twarzy.
4. **Żadne dwa sąsiadujące ujęcia twarzy nie mają tego samego kadru.** Naprzemienne przybliżenie ~7%
   zamienia skok w cięcie zamierzone. To proteza — docelowo sklejkę zasłania materiał z ekranu.
5. Cięcie dźwięku zawsze z krótkim wygaszeniem (~20 ms), nigdy w gołym przebiegu fali.
6. Przy planowaniu kolumny „Na ekranie”: **sklejki planuj tam, gdzie i tak wchodzi grafika lub zrzut** —
   wtedy nie widać ich wcale.

## Dźwięk
1. Muzyka pod głosem cicho (poziom do ustalenia na pierwszym filmie); bez efektów „whoosh” przy każdym cięciu.
