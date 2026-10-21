# Instrukcja dla sesji N8N_EA_System — folder `export/yt/`

> Ten projekt (YT_Channel) nie zmienia niczego w fabryce. Poniższe polecenie wklejasz w **sesji Claude Code projektu N8N_EA_System**.
> Szablony kart leżą w `YT_Channel/docs/export-yt-templates/`. Skopiuj je ręcznie albo wklej ich treść razem z poleceniem.

## Polecenie do wklejenia (jednorazowo)

```text
Utwórz w repo folder export/yt/ z podfolderami lessons/, funnel/, graveyard/ oraz plik export/yt/README.md,
który opisuje trzy rodzaje kart (szablony wklejam poniżej). Folder jest jedynym miejscem, które czyta projekt
YT_Channel (kanał YouTube) — tylko przez `git show` z gałęzi main.

Dopisz do CLAUDE.md tego projektu sekcję „Eksport dla kanału YT”:
- Przy przeglądzie nocy i przy handoffie oceń, czy zdarzenie jest lekcją wartą filmu. Jeśli tak — utwórz kartę
  export/yt/lessons/RRRR-MM-DD-slug.md wg szablonu lesson (publish_after = data + 2–4 tygodnie).
- Pierwszego dnia roboczego miesiąca utwórz export/yt/funnel/RRRR-MM.md z REALNYMI liczbami z Research Ledgera.
- Kartę export/yt/graveyard/QF-xxx.md twórz tylko dla strategii odrzuconej i nieprzeznaczonej do sprzedaży,
  zawsze z `graveyard: pending`; na `approved` zmienia wyłącznie właściciel.
- W kartach nigdy: nazw klientów, promptów generatora, JSON-ów strategii, parametrów strategii na sprzedaż,
  danych sprzedażowych, sekretów, adresów IP.
- Commit z kartą oznacz trailerem `Content: yes`.

Zacommituj.
```

## Prerekwizyty po stronie fabryki (do zrobienia w jej sesji)
1. **Research Ledger** z identyfikatorami `QF-xxx` i powodem odrzutu na każdym etapie. Bez niego raporty lejka nie mają źródła liczb.
2. **Źródło publikacji** zapisywane dla każdej strategii (autorzy, tytuł, rok). Potrzebne do serii „Paper vs Reality”.
3. **Miesięczny eksport** statystyk lejka do `export/yt/funnel/`.

## Jak to trafia do kanału
`YT_Channel/scripts/sync_context.py` (tryb `export_dir`) kopiuje pliki `.md` z `export/yt/` (gałąź `main`) do `YT_Channel/context/factory/` i dopisuje do feedu informację o nowych, zmienionych i usuniętych kartach. Karty z `publish_after` w przyszłości oznacza w feedzie jako `[EMBARGO do …]`.
