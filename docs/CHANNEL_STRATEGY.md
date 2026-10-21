# Strategia kanału YouTube

_Wersja 1.0 — 2026-10-21. Źródło decyzji: sesja planowania z 2026-10-20/21._

## 1. Tożsamość

- **Nazwa kanału:** „Imię Nazwisko — Systematic Trading Research” (marka osobista).
- **QuantInvest** = „my research lab”: miejsce, w którym powstają badania (opis kanału, strona z metodologią i Ledgerem). Nie przedstawiamy go jako firmy, która coś oferuje.
- **Pozycjonowanie:** *„I build and stress-test trading systems in public, from research papers to live algorithms, and I publish what fails.”*
- **Linie brandowe:**
  - *„Profitable backtests are easy to sell. I test whether they survive.”* (słowo „sell” odnosi się do innych)
  - *„Every update has to earn its way into production.”*
- **Teza:** sprawdzamy, czy twierdzenia przetrwają realne warunki. Nigdy nie mówimy „this EA makes X%”.
- **Przekaz „algo vs manual”:** podejście systematyczne jest mierzalne i testowalne. Nie twierdzimy, że algo zarabia więcej.

## 2. Odbiorca i język

- Od początkujących („czym jest algotrading”) po doświadczonych traderów, programistów i instytucje.
- **Film po angielsku** + **napisy EN i PL** w każdym filmie.
- Styl: *calm, analytical, precise*. Bez udawania akcentu, bez showmaństwa.

## 3. Skąd bierzemy content

| Źródło | Jak trafia do kanału | Gdzie leży u nas |
|---|---|---|
| Fabryka EA (N8N_EA_System) | Karty w `export/yt/` w fabryce → `scripts/sync_context.py` kopiuje je przez `git show` | `context/factory/` |
| Fabryka EA, commity | Commity z trailerem `Content: yes` + linia `Lekcja:` | `context/feed/` |
| Darmowe narzędzia (MQL5_Freelancer) | Karty `mql5/<Narzędzie>/VIDEO.md` | `context/tools/` |

Kanał nigdy nie czyta całych projektów. Z fabryki widzi wyłącznie to, co jej sesja świadomie zapisała do `export/yt/`. Szablony kart: `docs/export-yt-templates/`. Instrukcja dla sesji fabryki: `docs/N8N_EXPORT_INSTRUKCJA.md`.

**Embargo:** karta z `publish_after` w przyszłości nie może stać się filmem przed tą datą. Domyślne opóźnienie to 2–4 tygodnie: znamy wtedy wynik zdarzenia i nie zdradzamy bieżących prac.

## 4. Proporcja i formuła filmu

- **~70% filmów** pokazuje to, co dzieje się w projektach. **~30%** to tematy evergreen (Validation Gates, Tools).
- **Formuła filmu z projektów:**
  1. Co się u mnie wydarzyło (prawdziwa historia).
  2. Dlaczego to dotyczy każdego, kto testuje strategie (zasada ogólna).
  3. Jak to wykryć u siebie (praktyka dla widza).
  4. Werdykt i liczby (z Ledgera, z disclaimerem).

## 5. Filary

| Filar | Treść | Długość | Rytm |
|---|---|---|---|
| **The Funnel** | Miesięczny raport z Ledgera: ile hipotez weszło, gdzie i dlaczego odpadły, liczba prób | 10–15 min | 1×/mies. |
| **Paper vs Reality** | Jedna publikacja naukowa: wynik z artykułu vs wynik po kosztach, OOS, werdykt | 8–12 min | 1×/mies. |
| **Strategy Graveyard** | Pełny rozbiór odrzuconej strategii (tylko z `graveyard: approved`) | 8–12 min | co 1–2 mies. |
| **Validation Gates** | Jedna bramka metodologii na film; razem tworzą Methodology v1.0 | 8–10 min | 1×/mies. |
| **Tools** | Darmowe narzędzia MQL5 | 4–7 min + short | 1×/mies. |

- **Rytm:** 1 film tygodniowo, rotacyjnie z filarów, plus 3–5 shorts wyciętych z każdego filmu.
- **Seria ML/TFT** („Can ML adapt an EA without overfitting?”) wchodzi dopiero, gdy będą wyniki walidacji po reoptymalizacji. TFT pokazujemy jako hipotezę do sprawdzenia, nie obietnicę.

### Validation Gates — kolejność bramek (szkielet Methodology v1.0)
1. Data & logic integrity: look-ahead, survivorship, data snooping.
2. Backtest integrity: model wykonania, koszty, parytet silników.
3. Performance: dlaczego win rate prawie nic nie mówi; PF, expectancy, liczba transakcji.
4. Risk: DD, Calmar, Monte Carlo DD.
5. Robustness: wrażliwość parametrów (plateau vs szczyt), WFA.
6. Overfitting: liczba prób, Deflated Sharpe, PBO.
7. Execution: stres spreadu, poślizgu i prowizji.
8. Regimes oraz live vs backtest.

Werdykt to **PASS / CONDITIONAL / FAIL**, a nie punktowy „score”. Jeden krytyczny FAIL zatrzymuje ocenę.

## 6. Produkcja

### Nagrywanie hybrydowe
- **Twarz:** intro, kluczowe momenty i werdykt, czytane z teleprompteru.
- **Środek filmu:** ekran (Python, MT5, wykresy, diagram pipeline'u) i lektor czytany ze skryptu.

### Workflow skryptu (non-native speaker)
1. Temat i notatki po polsku (z karty lekcji / feedu).
2. Szkic skryptu EN w sekcjach odpowiadających rozdziałom (`docs/templates/script-template.md`).
3. Uproszczenie do języka mówionego: krótkie zdania, proste słowa.
4. Próbne czytanie, lista trudnych słów → zamiana na łatwiejsze.
5. Nagrywanie zdanie po zdaniu, cięcie pauz w montażu.
6. Napisy: EN dokładnie wg nagrania, PL tłumaczone ze skryptu (pliki `.srt`).

### Sprzęt — start za 0 zł
- telefon lub kamera laptopa,
- mikrofon słuchawek lub telefonu w cichym pomieszczeniu,
- światło dzienne z okna przed twarzą,
- OBS (nagrywanie ekranu), DaVinci Resolve (montaż i napisy), Canva Free (miniatury),
- teleprompter jako darmowa strona lub aplikacja.

Pierwszy możliwy zakup (mikrofon USB) dopiero po 10–20 filmach i tylko wtedy, gdy dźwięk okaże się wąskim gardłem.

### Standard publikacji (każdy film)
- **Rozdziały z timestampami** w opisie: pierwszy `0:00`, co najmniej 3 rozdziały, każdy ≥10 s (`docs/templates/description-template.md`).
- **Napisy EN + PL.**
- **Disclaimer** przy każdym wyniku.
- **Linki wyłącznie niesprzedażowe** (patrz §7).
- Pierwsze filmy 6–10 min. Ocena formatów po 10 filmach.

## 7. Granice

**Dane**
- Strategie, które przetrwały (kandydaci do sprzedaży): tylko zagregowane metryki, bez reguł, parametrów i JSON-ów.
- Strategie odrzucone: pełna logika dozwolona, ale tylko z kartą Graveyard `approved`.
- Liczby publiczne wyłącznie z Ledgera. Nigdy ilustracyjne ani „przykładowe”.
- Bez klientów i zleceń, promptów generatora, danych sprzedażowych i płatności.
- Disclaimer: *„Historical results, not investment advice. Past performance does not guarantee future results.”*

**Tytuły**
- Zakazane słowa: „only”, „secret”, „AI”, „AI-powered”, „100%”, „holy grail”, „guaranteed”. Bez kwot zysku.
- Liczba w tytule tylko wtedy, gdy jest realna i opisuje proces (np. „23 strategies in, 2 survived”).

**Język sprzedaży — faza budowania zaufania** (pierwsze kilka do kilkunastu miesięcy, do decyzji właściciela)
- W odniesieniu do siebie i QuantInvest zakazane: „we/I sell”, „buy”, „our product”, „offer”, „discount”, „get my EA”, „link to purchase” i ich warianty.
- Zakaz obejmuje tytuły, skrypty, opisy, przypięte komentarze i plansze końcowe.
- W odniesieniu do innych wolno („they sell profitable backtests”, „EA vendors claim…”).
- CTA tylko niesprzedażowe: darmowe narzędzia w Code Base, profil mql5.com, Methodology i Ledger na stronie, newsletter.
- Audyt jako usługa i jego cennik nie pojawiają się do czasu publikacji Methodology v1.0.

**Regulamin MQL5**
- Nie wyciągamy klientów z MQL5 Freelance poza platformę.
- Opis Signals nie służy do reklamy usług.

## 8. Cele (12 miesięcy, zdywersyfikowane)
Ruch na mql5.com, wiarygodność wobec instytucji, później sprzedaż EA (po fazie zaufania) i własna lista mailingowa. Kanał jest maszyną wiarygodności, a nie biznesem z AdSense.
