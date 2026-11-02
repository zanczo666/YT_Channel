---
slug: _test-nagranie
filar: Validation Gates
zrodlo: nagranie testowe pipeline'u (nie z karty)
publish_after: brak
tytul_roboczy: The ten-minute test most strategies fail
dlugosc_docelowa: ~1,5 min
slowa_szacunkowo: 165
---

> **Nie do publikacji.** Nagranie próbne do kalibracji pipeline'u montażu (C1–C5) na prawdziwym głosie.
> Treść jest sensowna i bez liczb, więc gdyby test wypadł dobrze, materiał da się później przerobić na shorta.

## [0:00] Hook
| ID | EN (mówione) | PL (napisy) | Na ekranie |
|---|---|---|---|
| L001 | There is one test I run before I trust any trading system. | Jest jeden test, który robię, zanim zaufam jakiemukolwiek systemowi tradingowemu. | TWARZ |
| L002 | It takes about ten minutes, and most strategies do not survive it. | Zajmuje jakieś dziesięć minut i większość strategii go nie przeżywa. | TWARZ |

## [~0:15] What the test is
| ID | EN (mówione) | PL (napisy) | Na ekranie |
|---|---|---|---|
| L003 | Split your historical data into two parts before you start. | Podziel dane historyczne na dwie części, zanim zaczniesz. | EKRAN: podział danych |
| L004 | Build and tune the strategy on the first part only. | Buduj i strój strategię wyłącznie na pierwszej części. | EKRAN: podział danych |
| L005 | The second part stays closed until the strategy is finished. | Druga część zostaje zamknięta, dopóki strategia nie jest gotowa. | EKRAN: podział danych |
| L006 | Then you run it once on the second part, and you do not touch it again. | Potem uruchamiasz ją raz na drugiej części i więcej jej nie dotykasz. | TWARZ |

## [~0:45] Why it matters
| ID | EN (mówione) | PL (napisy) | Na ekranie |
|---|---|---|---|
| L007 | Every parameter you tune is a small decision based on the data. | Każdy strojony parametr to mała decyzja podjęta na podstawie danych. | TWARZ |
| L008 | Enough of those decisions and the strategy learns the past by heart. | Wystarczy ich dość dużo i strategia uczy się przeszłości na pamięć. | GRAFIKA: equity IS/OOS |
| L009 | A curve that looks perfect on known data tells you nothing. | Krzywa, która wygląda idealnie na znanych danych, nie mówi nic. | GRAFIKA: equity IS/OOS |
| L010 | The second half is the only part that was never allowed to vote. | Druga połowa to jedyna część, która nigdy nie miała prawa głosu. | TWARZ |

## [~1:10] Close
| ID | EN (mówione) | PL (napisy) | Na ekranie |
|---|---|---|---|
| L011 | Run this split on your own system this week and see what happens. | Zrób ten podział na swoim systemie w tym tygodniu i zobacz, co wyjdzie. | TWARZ |
| L012 | Historical results, not investment advice. Past performance does not guarantee future results. | Wyniki historyczne, nie porada inwestycyjna. Wyniki z przeszłości nie gwarantują przyszłych. | TWARZ |

---

## Jak to nagrać (instrukcja do testu)

Nagrywasz **jednym ciągiem**, bez zatrzymywania kamery. Pipeline ma sam znaleźć zdania i wybrać dobre ujęcia,
więc im bardziej naturalnie (z pomyłkami), tym lepszy test.

1. **Pauza na start.** Włącz nagrywanie, odczekaj 2–3 sekundy w ciszy, dopiero potem pierwsze zdanie.
2. **Czytaj zdanie po zdaniu**, robiąc **pół sekundy ciszy między zdaniami**. Cisza to dla pipeline'u granica
   ujęcia — bez niej cięcia wypadają w środku słowa.
3. **Trzy celowe pomyłki** (to jest właściwy przedmiot testu — bez nich sprawdzamy tylko połowę):
   - **L005** — zacznij zdanie, urwij w połowie, powiedz „sorry” i powtórz **całe** zdanie od początku.
   - **L008** — przeczytaj całe, ale przekręć słowo (np. „learns the past by hand”), potem powtórz poprawnie.
   - **L011** — przeczytaj poprawnie, zrób pauzę, powiedz „one more time” i przeczytaj **jeszcze raz**,
     tym razem żywiej. Sprawdzamy, czy pipeline bierze **ujęcie późniejsze**.
4. **Nie wycinaj niczego sam.** Pomyłki mają zostać w pliku.
5. **Pauza na koniec.** Po ostatnim zdaniu odczekaj 2–3 sekundy przed zatrzymaniem nagrywania.

Czego test nie sprawdza: oświetlenia ani kadru. Wystarczy, że widać twarz i słychać głos.
Nagrywaj **tym sprzętem, którym będziesz nagrywać naprawdę** — kalibrujemy dźwięk pod Twój mikrofon,
więc nagranie z innego telefonu niż docelowy nie da nam tego, o co chodzi.
