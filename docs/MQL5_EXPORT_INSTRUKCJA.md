# Instrukcja dla sesji MQL5_Freelancer — karty `VIDEO.md`

> Ten projekt (YT_Channel) nie zmienia niczego we freelance. Poniższe polecenie wklejasz w **sesji Claude Code projektu MQL5_Freelancer**.
> Skrypt `scripts/sync_context.py` czyta wyłącznie `mql5/<Narzędzie>/VIDEO.md` z gałęzi `main` i commity dotykające tych katalogów.
> Narzędzie bez karty jest dla kanału niewidoczne (opt-in), a pliki klientów nigdy nie trafiają do feedu.

## Polecenie do wklejenia (jednorazowo)

```text
Dla każdego narzędzia w mql5/, które jest opublikowane jako darmowe w MQL5 Code Base
(IchimokuProPanel, RiskPositionSizeCalculator, SessionSpreadAlert, SpreadMonitorScalpers), utwórz plik
mql5/<Narzędzie>/VIDEO.md według szablonu poniżej. To karta dla kanału YouTube (angielskojęzycznego,
z napisami PL). Pisz po polsku, poza polem „Hook (EN)”.

Zasady treści karty:
- Tylko narzędzia własne i darmowe. Nigdy nazw klientów, zleceń, kwot, korespondencji ani prac dla kogokolwiek.
- Bez linków do płatnych produktów i bez języka sprzedaży („kup”, „oferta”, „zniżka”).
- Bez sekretów, kluczy, adresów IP.

Dopisz do CLAUDE.md tego projektu linię:
- Przy publikacji lub aktualizacji darmowego narzędzia w mql5/ utwórz lub zaktualizuj mql5/<Narzędzie>/VIDEO.md
  według szablonu (problem, dla kogo, zasada ogólna, demo, przed/po, haczyki, co pokazać / czego nie, link, wersja).
  Karta nie może zawierać niczego o klientach i zleceniach.

Zacommituj na main.

Szablon:

# <NazwaNarzędzia>
Wersja: <x.y> (RRRR-MM-DD)
Link: <adres publikacji w MQL5 Code Base>
Problem: <jaki ból tradera to rozwiązuje — jedno zdanie>
Dla kogo: <początkujący / zaawansowany / programista MQL5>
Zasada ogólna: <czego uczy niezależnie od narzędzia, np. „wielkość pozycji ważniejsza niż wejście”>
Hook (EN): <jedno zdanie na pierwsze 15 sekund filmu>
Demo (60 s): <co dokładnie pokazać na wykresie, krok po kroku>
Przed/po: <jak to wyglądało bez narzędzia>
Haczyki: <nieoczywiste ustawienia, typowe błędy użytkowników>
Pokazać na ekranie: <panel, ustawienia, ewentualnie konkretny fragment kodu — plik i funkcja>
Nie pokazywać: <np. elementy wspólne z pracami dla klientów>
```

## Opcjonalnie: `docs/OVERVIEW.md` (wciąż brakuje w obu projektach)

```text
Utwórz docs/OVERVIEW.md (max 60 linii): czym jest projekt, architektura w punktach, co już działa, co jest w toku.
Bez sekretów, kluczy, adresów IP, nazw klientów i szczegółów zleceń. Zacommituj na main.
```

`CLAUDE.md` kanału importuje ten plik przy starcie każdej sesji, więc krótki i bez danych wrażliwych.

## Jak to trafia do kanału
`sync_context.py` (tryb `video_cards`) kopiuje karty do `YT_Channel/context/tools/<Narzędzie>.md`, a commity dotykające `mql5/<Narzędzie>/` dopisuje do tygodniowego feedu.
