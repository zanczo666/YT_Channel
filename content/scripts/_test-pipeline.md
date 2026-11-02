---
slug: _test-pipeline
filar: Validation Gates
zrodlo: nagranie syntetyczne (scripts/nagranie_probne.py)
publish_after: brak
tytul_roboczy: Out of sample split — test nagrania próbnego
dlugosc_docelowa: 1 min
slowa_szacunkowo: 90
---

> **Nie do publikacji.** Plik testowy pipeline'u montażu; generuje go `scripts/nagranie_probne.py`.

## [0:00] Hook
| ID | EN (mówione) | PL (napisy) | Na ekranie |
|---|---|---|---|
| L001 | Most backtests that look great never survive a single honest test. | Większość świetnie wyglądających backtestów nie przeżywa jednego uczciwego testu. | TWARZ |
| L002 | In this video I run that test, and I show you the result either way. | W tym filmie przeprowadzam ten test i pokazuję wynik niezależnie od tego, jaki wyjdzie. | TWARZ |

## [~0:15] What happened
| ID | EN (mówione) | PL (napisy) | Na ekranie |
|---|---|---|---|
| L003 | The first thing we check is whether the edge holds out of sample. | Najpierw sprawdzamy, czy przewaga utrzymuje się poza próbą. | EKRAN: podział danych |
| L004 | I split the data into two halves and I never touch the second one. | Dzielę dane na dwie połowy i drugiej nigdy nie dotykam. | EKRAN: podział danych |
| L005 | The strategy made money in sample and lost money out of sample. | Strategia zarabiała w próbie i traciła poza próbą. | GRAFIKA: equity IS/OOS |

## [~0:35] Why it matters to you
| ID | EN (mówione) | PL (napisy) | Na ekranie |
|---|---|---|---|
| L006 | That gap is the whole story, and it is the most common failure I see. | Ta różnica to cała historia i najczęstsza porażka, jaką widuję. | TWARZ |
| L007 | You can run the same split on your own system in about ten minutes. | Ten sam podział możesz zrobić u siebie w jakieś dziesięć minut. | EKRAN: kod |

## [~0:50] Disclaimer
| ID | EN (mówione) | PL (napisy) | Na ekranie |
|---|---|---|---|
| L008 | Historical results, not investment advice. Past performance does not guarantee future results. | Wyniki historyczne, nie porada inwestycyjna. Wyniki z przeszłości nie gwarantują przyszłych. | TWARZ |
