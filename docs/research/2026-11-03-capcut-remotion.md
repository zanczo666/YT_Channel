# Co da się wziąć z „Claude Code + CapCut/Remotion” — wnioski do pipeline'u

_2026-11-03. Źródła: dwa filmy wskazane przez właściciela, obejrzane przez `scripts/yt_watch.py`
(Gemini, obraz + dźwięk). Surowe analizy w scratchpadzie sesji, nie w repo._

| Film | Temat |
|---|---|
| `LS4CFPLRlRU` | Claude Code steruje CapCutem: cięcia, napisy, grafiki, B-roll |
| `8oIFBQ9BhVU` | Claude Code + Remotion: grafiki ruchome, LUT-y, liczniki |

## Wniosek główny

**Mechanika z pierwszego filmu jest dla nas bezużyteczna, treść z drugiego — nie.**

CapCut nie ma publicznego API. Pokazana „integracja” to skrypt, który ubija proces CapCuta, wpisuje dane
do nieudokumentowanego `draft_content.json` w `~/Movies/CapCut/User Data/Projects/com.lveditor.draft/`
i restartuje aplikację przez AppleScript. Format zmienia się między wersjami, działa tylko na macOS/Windows,
a nasz worker to jednorazowy Linux. Drugi film **wprost przyznaje**, że między Claude a CapCutem nie ma
żadnej integracji — człowiek ręcznie przeciąga wygenerowane pliki do GUI.

## Czego oni używają, a my już to mamy

| Ich krok | Nasz odpowiednik | Uwaga |
|---|---|---|
| Deepgram (płatna transkrypcja słowo po słowie) | C2 `faster-whisper`, lokalnie | u nas bez kosztu i bez wysyłania nagrania na zewnątrz |
| Wycinanie ciszy i złych ujęć | C3 `align.py` | **nasze jest mocniejsze** — patrz niżej |
| Napisy | C8, EN + PL | oni mają jeden język |
| Nakładki z kanałem alfa | C7 (PNG RGBA + `overlay`) | identyczna technika, bez ProRes |
| Ręczna korekta w GUI | EDL CMX3600 → DaVinci (C4) | nasza furtka awaryjna |
| Styl z zatwierdzonych filmów | `docs/EDITING_RULES.md` | ta sama pętla |

**Różnica przy złych ujęciach jest zasadnicza.** Oni zgadują z transkrypcji, co było wpadką (długa pauza,
powtórzona fraza). My porównujemy nagranie ze **scenariuszem** — wiemy, co miało paść, więc przy trzech
ujęciach L012 świadomie bierzemy trzecie. Ich metoda nie odróżni powtórzenia po wpadce od celowej repetycji
retorycznej, a przy naszym formacie (zdanie po zdaniu z ID) to byłby krok wstecz.

## Co bierzemy — konkretnie

### 1. LUT jako plik `.cube` → odblokowuje C6

Model językowy potrafi wygenerować poprawny plik `.cube` (trójwymiarowa tablica przekształceń koloru),
a FFmpeg ma filtr **`lut3d`** — sprawdzone, jest w naszej instalacji. To cała korekcja barwna bez GUI:

```
-vf lut3d=file=styl.cube
```

To jedyny element z obu filmów, który wprost domyka coś, co u nas stoi (C6 🟡). Zastrzeżenie: „kinematyczny,
pastelowy” to kwestia gustu, nie matematyki — LUT trzeba obejrzeć na prawdziwej klatce, nie przyjąć w ciemno.
Dlatego C6 powinien zapisywać klatkę przed/po do zatwierdzenia.

### 2. Grafiki mają się ruszać

To jest odpowiedź na uwagę właściciela po pierwszym montażu („sztywno, brak płynności”). C7 renderuje
nieruchomy PNG i go przenika. Oni renderują animację. **Nie potrzebujemy do tego Remotion:** `graphics.py`
może wyrenderować sekwencję klatek w Pillow (3 s przy 30 fps to 90 PNG — grosze) i nałożyć ją tak jak teraz.
Wykres equity, który się *rysuje*, zamiast pojawiać się gotowy.

Do tego `zoompan` (jest w naszym FFmpeg) daje powolny najazd na nieruchome plansze — efekt „Ken Burns”.

### 3. Plansze sekcji

Oni wstawiają karty „Step 1/2/3” tam, gdzie padają te słowa. My mamy tytuły rozdziałów w C9, ale **tylko
jako metadane YouTube'a** — nic nie pojawia się na ekranie. Dane już są; brakuje szablonu i wstawienia.
Przy okazji plansza daje naturalne miejsce na sklejkę, czyli znowu: mniej sztywności.

### 4. Podkreślanie tekstu na zrzucie publikacji (Tesseract)

Technika z drugiego filmu: OCR znajduje współrzędne słów na zrzucie, a potem narysowany zakreślacz
przejeżdża po wskazanym zdaniu. Dla kanału, który z założenia idzie **od publikacji naukowych do działających
algorytmów**, to jest trafione w sedno — podkreślenie jednego zdania w abstrakcie zamiast opowiadania o nim.
Tesseract jest na Linuksie, a sam zakreślacz narysujemy w Pillow (nie trzeba `rough.js` ani Node'a).

## Czego świadomie nie bierzemy

- **B-roll generowany przez AI** (Kie, Grok Imagine). Na kanale o systematycznym tradingu generyczne obrazki
  podkopują dokładnie tę wiarygodność, którą kanał ma budować. Naszym B-rollem są krzywe equity, tabele
  z Ledgera i kod na ekranie — czyli to, co C7 robi **z prawdziwych danych** (zasada z CLAUDE.md: liczby
  publiczne wyłącznie z Ledgera / kart fabryki).
- **Remotion.** Działałby na Linuksie (Node 18+, headless Chrome, przy WebGL `--gl=angle --concurrency=1`),
  ale to ciężka zależność na workerze. Nasze typy grafik — equity, lejek, metryki, cytat — robi Pillow.
  Do rozważenia dopiero, gdyby kanał poszedł w kinetyczną typografię.
- **Licznik z pliku SRT rozpędzony dziesięciokrotnie.** Sprytna sztuczka pod GUI CapCuta; u nas to `drawtext`
  albo zwykła sekwencja klatek.
- **CapCut jako taki.** Zamknięty format, tylko macOS/Windows, wymaga ubijania i restartowania aplikacji
  przy każdej zmianie.

## Uczciwie o źródłach

Pierwszy film kończy się sprzedażą kursu; deklaracje „10× szybciej, 1000× taniej od montażysty” to marketing,
a sam autor przyznaje, że zbudowanie tego od zera to **20–30 godzin**. Drugi jest rzetelniejszy: pokazuje
też **porażki** — brak kanału alfa w MP4 (stąd ProRes 4444), awarię renderu map bez flag WebGL, poszarpaną
animację wektorową, wysokie zużycie tokenów. To ten rodzaj szczegółu, który świadczy, że autor naprawdę to robił.

## Co z tego wchodzi do planu

| Element | Status | Z tej analizy |
|---|---|---|
| C6 korekcja barwna | 🟡 → do zrobienia | `lut3d` + klatka przed/po do zatwierdzenia |
| C7 grafiki | ✅ → rozszerzyć | sekwencja klatek zamiast nieruchomego PNG; `zoompan` |
| C7 plansze sekcji | nowy | tytuły z C9, szablon jak pozostałe |
| C7 zakreślacz na publikacji | nowy, później | Tesseract + Pillow |
