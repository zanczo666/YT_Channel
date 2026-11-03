# Standard nagrania

Wnioski z nagrań próbnych 2026-11-02 i 2026-11-03. Reguły montażowe: `docs/EDITING_RULES.md`, przesył: `docs/SYNC.md`.

## Sprzęt i ustawienia
- Telefon **poziomo, na statywie**. Z ręki tło pływało do 42 px na 0,1 s, ze statywu stoi w miejscu.
- 1080p, 30 kl./s. HDR, tryb „beauty” i filtry wyłączone.
- Dźwięk: wejście audio sprawdź w aparacie. Podłączona słuchawka Bluetooth nie oznacza, że aparat z niej nagrywa
  (nagranie 2026-11-03 miało stereo i pasmo powyżej 9 kHz, czyli szło z mikrofonu telefonu).

## Kadr
- Obiektyw **na wysokości oczu albo trochę wyżej**. Od dołu widać sufit, podbródek i szyję.
- Zapas nad głową: montaż przybliża co drugie ujęcie o 7%, więc kadruj luźniej, niż wydaje się potrzebne.
- Oczy mniej więcej w górnej 1/3 kadru, ramiona bez wyciągniętej ręki.
- Tło spokojne: bez świecącej lampy w kadrze i przedmiotów, które przyciągają wzrok.
- Tekst z telepromptera jak najbliżej obiektywu.

## Światło i pokój
- Główne światło przed Tobą, nie nad głową ani z boku. Świecące czoło: odsuń albo rozprosz lampę.
- Pomieszczenie miękkie: dywan, zasłony, regały skracają pogłos. C5 go nie usunie.
- Wentylator i powiadomienia wyłączone, okno zamknięte.

## Przebieg
1. Nagrywaj **jednym ciągiem**, bez zatrzymywania.
2. Na starcie **5 s ciszy**: to pomiar szumu pokoju.
3. Zdanie po zdaniu, z **pół sekundy ciszy** między nimi.
4. Po pomyłce zrób krótką pauzę i powtórz **całe zdanie od początku**. Zostaje ostatnie czyste ujęcie.
5. Nie przycinaj pliku.
6. Na końcu 3 s ciszy.

## Po nagraniu
- Nazwa pliku musi zaczynać się od **`yt`** i kończyć na `.mp4`, np. `yt_<slug>.mp4`. Inne pliki nie przejdą przez filtr.
- Telefon zostaw w Wi-Fi z włączonymi Tailscale i Syncthingiem do czasu, aż plik dotrze do `~/inbox/`.
