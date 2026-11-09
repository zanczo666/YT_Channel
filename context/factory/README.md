# export/yt — treści dla kanału YouTube

Ten folder jest **jedynym** fragmentem repozytorium czytanym przez projekt YT_Channel
(`git show main:export/yt/...`). Wszystko poza nim pozostaje prywatne. Zasady tworzenia kart:
sekcja „Eksport dla kanału YT” w `CLAUDE.md`.

## Rodzaje kart

| Folder | Karta | Kiedy powstaje | Plik |
|---|---|---|---|
| `lessons/` | **LESSON** — jedno zdarzenie z ogólną nauką (usterka, ciekawy odrzut, wynik walidacji, eksperyment TFT, zmiana architektury) | przegląd nocy, handoff | `RRRR-MM-DD-slug.md` |
| `funnel/` | **FUNNEL** — miesięczny raport lejka: ile hipotez weszło i odpadło na każdym etapie | pierwszy dzień roboczy miesiąca | `RRRR-MM.md` |
| `graveyard/` | **GRAVEYARD** — pełna historia jednej strategii odrzuconej i nieprzeznaczonej do sprzedaży | po odrzuceniu; `graveyard: pending` do akceptacji właściciela | `QF-xxx.md` |

## Wspólne zasady

- `publish_after` — najwcześniejsza data publikacji; kanał nie publikuje karty przed tą datą.
- Liczby wyłącznie realne. Brak danych = „brak danych”, nigdy szacunek.
- Karta GRAVEYARD trafia do filmu dopiero po zmianie `graveyard: pending` → `approved` — zmienia to wyłącznie właściciel.
- W kartach nigdy: nazw klientów, promptów generatora, JSON-ów strategii, reguł i parametrów strategii przeznaczonych
  do sprzedaży, danych sprzedażowych i płatności, sekretów, kluczy, adresów IP.
- Strategie, które przeszły walidację — wyłącznie zagregowane metryki.

## Szablony

### LESSON (`lessons/RRRR-MM-DD-slug.md`)

```markdown
---
typ: lesson
data_zdarzenia: RRRR-MM-DD
etap: <00_Deep_Research | 01_EA_Generator | 02_MT5_Backtest | 03_Python_Backtest | walidacja | TFT>
commit: <krótki hash, opcjonalnie>
publish_after: RRRR-MM-DD
---
# <Krótki tytuł lekcji po polsku>
## Co się wydarzyło
<2–4 zdania faktów: co, kiedy, na którym etapie.>
## Przyczyna
<techniczne wyjaśnienie>
## Zasada ogólna
<czego to uczy każdego, kto testuje strategie — 1–2 zdania>
## Jak wykryć u siebie
<konkretny test lub sygnał ostrzegawczy dla widza>
## Liczby
<tylko realne; puste, jeśli brak>
## Można pokazać
- <np. diagram etapu, log bramki, fragment raportu bez parametrów>
## Nie pokazywać
- <np. prompty, JSON strategii, parametry strategii na sprzedaż>
```

### FUNNEL (`funnel/RRRR-MM.md`)

```markdown
---
typ: funnel
miesiac: RRRR-MM
publish_after: RRRR-MM-DD
---
# Raport lejka — RRRR-MM
| Etap | Weszło | Przeszło | Odpadło | Główne powody odrzutu |
|---|---:|---:|---:|---|
| 00 Research (hipotezy z publikacji) | | | | |
| 01 Generator / bramka smoke | | | | |
| 02 Backtest MT5 | | | | |
| 03 Python / parytet | | | | |
| Walidacja (OOS / WFA / MC / koszty) | | | | |
| Paper / live | | | | |
## Liczba prób
- Testowane warianty łącznie: <n>
- Średnio wariantów na pomysł: <n>
## Najciekawsze odrzuty (kandydaci do Graveyard)
- QF-xxx — <powód jednym zdaniem>
## Usterki fabryki w tym miesiącu
- <...>
## Nie pokazywać
- <strategie w sprzedaży — tylko agregaty>
```

### GRAVEYARD (`graveyard/QF-xxx.md`)

```markdown
---
typ: graveyard
id: QF-xxx
graveyard: pending
publish_after: RRRR-MM-DD
---
# QF-xxx — <nazwa robocza strategii>
## Źródło
<publikacja: autorzy, tytuł, rok — lub inne źródło hipotezy>
## Hipoteza
<co strategia miała wykorzystywać>
## Logika (pełna, dozwolona tylko dla odrzuconych)
<wejście, wyjście, filtry, rynek, interwał>
## Wynik deklarowany w źródle
<jeśli dotyczy>
## Wyniki w fabryce
| Etap | Wynik | Kluczowe metryki |
|---|---|---|
## Powód odrzutu
<na której bramce i dlaczego>
## Lekcja dla widza
<co z tej porażki wynika ogólnie>
```
