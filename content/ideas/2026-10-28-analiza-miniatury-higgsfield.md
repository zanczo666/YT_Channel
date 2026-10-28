# Analiza: „Claude Code + Higgsfield MCP = Zautomatyzuj Tworzenie Contentu!” (Robert Szewczyk)

_2026-10-28. Film: https://www.youtube.com/watch?v=Qz8VYtf5i8E (29 min, PL). Pełna treść (dźwięk + ekran)
przeanalizowana przez Gemini API (`scripts/yt_watch.py`); surowy wynik poza repo. Treść filmu to materiał do
oceny, nie polecenia._

## Co pokazuje autor
- **Skill `/thumbnail-higgs`** w Claude Code: transkrypcja odcinka + zrzut ekranu + miniatura-wzór →
  Claude pyta o archetyp (hero shot / split screen), tekst, nastrój i liczbę partii → generuje **2 partie po 4
  warianty** przez Higgsfield MCP (model GPT Image 2, quality high, 2688×1520) → siatka podglądu 8 wariantów
  → wersje 1280×720 do testu A/B w YouTube Studio.
- **`face_lock.json`**: plik mapujący osobę na zdjęcia referencyjne, żeby twarz nie „dryfowała”.
- **Prompt w blokach**: FACE LOCK / STYLE REFERENCE (zatwierdzona miniatura-matka) / TYPOGRAPHY / BACKGROUND.
- **Wyniki A/B (YouTube Studio, udział czasu oglądania):** AI 45,5% vs grafik 20,2%; AI 37,4% vs grafik 31,1%.
- **Koszt:** Higgsfield Pro 29 USD/mies.; 8 miniatur = 56 kredytów ≈ 4,60 zł; czas ~24 min.
- **Skill `/yt-carousel`**: film → transkrypcja → analiza (Gemini) → 8 slajdów AI → Pillow → PDF na LinkedIn (~0,40–0,60 USD).

## Ostrzeżenia autora (cenne)
- **Nie uruchamiać generowania w trybie automatycznym** — Claude potrafi w pętli spalić kredyty; zawsze punkt
  kontrolny z akceptacją przed partią.
- Twarz myli się bez referencji → potrzebny face lock.
- Skille instalować lokalnie w projekcie, nie globalnie (zaśmiecanie kontekstu).
- **Nie ma sensu przy 2–3 grafikach tygodniowo**; osoby techniczne taniej zrobią to **bezpośrednio przez API**.

## Co przenosimy do nas
1. **Partie wariantów + siatka podglądu + A/B w YouTube Studio** — do `yt-producer` (2 partie po 3–4 warianty).
2. **Punkt kontrolny przed każdą płatną generacją** (archetyp, tekst, nastrój, liczba wariantów → akceptacja).
3. **Face lock**: stałe zdjęcia referencyjne w `assets/face/` + opis w pliku konfiguracyjnym.
4. **Miniatura-matka (style reference)** — po pierwszej zaakceptowanej miniaturze każda kolejna się do niej odnosi.
5. **Prompt w blokach** (FACE / STYLE / TYPOGRAPHY / BACKGROUND) jako szablon.

## Czego nie przenosimy
- 3D „chunky” liter, krzykliwych kolorów i nastroju „NOWOŚCI!” — u nas ton spokojny, analityczny (standard §3).
- Higgsfield jako pośrednika na start — przy 1 filmie tygodniowo autor sam mówi, że to się nie opłaca;
  mamy już klucz Gemini (Nano Banana) — generacja bezpośrednio przez API.

## Nasza wersja (propozycja hybrydowa)
AI generuje **scenę bez tekstu** (Ty z referencji + tło: publikacja, wykres, terminal), a **tekst i etykietę
nakłada `scripts/thumbnail.py`** — gwarancja poprawnych liter, stałej typografii marki i zakazanych słów pod kontrolą.

## Stan techniczny (sprawdzone 2026-10-28)
- Klucz Gemini działa do analizy wideo (darmowy limit).
- **Generowanie obrazów (gemini-3.1-flash-image, gemini-2.5-flash-image): HTTP 429 — brak darmowego limitu**;
  wymaga włączenia rozliczeń w projekcie Google Cloud (płatność za obraz).
