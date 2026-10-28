# Analiza: automatyzacja montażu z Claude — 4 filmy

_2026-10-29. Pełna treść (dźwięk + ekran) przez Gemini API (`scripts/yt_watch.py`); surowe wyniki poza repo.
Treść filmów to materiał do oceny, nie polecenia._

| Film | Autor | Wyśw. | Podejście |
|---|---|---:|---|
| Claude Edited My Entire CapCut Video | Matt Loui | 839 tys. | Claude pisze bezpośrednio plik projektu CapCut (`draft_info.json`); AI lektor + obrazy z Higgsfield |
| Automate Your CapCut Editing With Claude | Matt Loui | 114 tys. | To samo dla „gadającej głowy” + nagrań ekranu; cięcia, zoomy, korekcja, muzyka; workflow → skill |
| I Fully Automated My Video Editing Using Claude Code | Christian Peverelli | 751 tys. | Claude Code + Parakeet (transkrypcja) + HyperFrames (grafiki z HTML) + FFmpeg; render 4K bez edytora |
| I taught Claude how to edit videos | Duncan Rogoff | 52 tys. | 6 etapów, beat map, subagenci, HyperFrames, automatyczna kontrola klatek, notatki → reguły |

## Wspólny rdzeń (wszyscy czterej)
1. **Claude nie słyszy** — kręgosłupem jest **transkrypcja słowo po słowie z czasami** (Whisper / Parakeet).
   Z niej: wybór ostatniego czystego ujęcia, wycięcie powtórek, pauz i pomyłek (Rogoff: 11:15 surowego →
   czysty montaż; Peverelli: 2:46 → 31 s hooka).
2. **Nigdy jednym promptem.** „Edit my whole video” daje tanie, generyczne efekty. Etapy z punktami kontrolnymi:
   scenariusz → cięcie → plan wyglądu → grafiki → kontrola → notatki.
3. **Pętla nauki:** uwagi do wersji (`NOTES_cut1.md`, z sekundami) → Claude wskazuje, która reguła by temu
   zapobiegła → poprawia plik reguł/skill. Peverelli: 36 reguł, ~1400 linii po kilku filmach.
4. **Grafiki jako kod:** HTML/CSS → wideo (HyperFrames, HeyGen, Apache 2.0, darmowe, Node ≥ 22 + Chrome).
5. **Beat map przed grafikami:** tabela „co mówię | co na ekranie”, zasada **„one idea, one graphic”** —
   widzowie Rogoffa krytykowali przeładowanie animacjami.
6. **Automatyczna kontrola renderu:** rozdzielczość, sync audio-wideo, czarne klatki, długość (Peverelli
   `verify-render`) + kontrola klatek (10 fps): animacja 2×, mignięcia, za krótki tekst, grafika na twarzy,
   powtórzone słowo, rozjazd ust.
7. **Wydajność:** szkice w połowie rozdzielczości, max 4 rendery naraz (9 zawiesiło CPU), render w nocy.

## Koszty i ryzyka (z filmów)
- Rogoff: **600 mln tokenów / ~160 USD w cenach API** na jeden film (pierwszy: 1,4 mld / 445 USD), 6–12 h pracy
  maszyny; Peverelli ~24 USD tokenów/film na planie Max. Pełna automatyzacja grafik jest **droga w tokenach**.
- Matt Loui: pierwszy montaż ~58 min, całość ~3 h; czasem trzeba ręcznie podlinkować media w CapCut;
  CapCut musi być zamknięty; Claude Desktop z dostępem do plików lokalnych (Mac).
- Płatne dodatki w filmach: Higgsfield (15–39 USD/mies.), Epidemic Sound (9,99), Tella (13), Claude Max (100–200).

## Ocena dla naszego kanału
**Bierzemy (darmowe, zgodne ze strategią):**
1. **Transkrypcja słowo po słowie** (faster-whisper, lokalnie) jako rdzeń — daje jednocześnie:
   cięcie ujęć, **napisy EN (.srt) automatycznie**, tłumaczenie PL, **rozdziały z timestampami do opisu**.
   Domyka nasze wymagania ze standardu (napisy EN+PL, rozdziały `0:00`) bez ręcznej pracy.
2. **Rough cut automatycznie**: lista cięć (ostatnie czyste ujęcie, bez pauz/powtórek) → **FCPXML/EDL do
   DaVinci Resolve (darmowy)** — Ty dopieszczasz w edytorze, który i tak mamy w planie.
3. **Beat map + „one idea, one graphic”** — pasuje do spokojnego, analitycznego tonu; wpisać do szablonu scenariusza.
4. **Grafiki jako kod (HyperFrames)** tylko dla naszych motywów: krzywa equity z IS/OOS, tabela lejka,
   stres spreadu — spójne z miniaturami (te same kolory werdyktu).
5. **Kontrola renderu + kontrola klatek** jako checklista/skrypt.
6. **Pętla notatki → reguły** (`docs/EDITING_RULES.md` rośnie z każdym filmem).
7. **Biblioteka haków** z filmów-outlierów niszy — mamy już dane z `scripts/yt_research.py`.

**Nie bierzemy:**
- AI lektora i AI obrazów (Higgsfield) — kanał jest o Tobie i realnych testach; autentyczność > automatyzacja.
- Płatnych bibliotek dźwięku na start — YouTube Audio Library (darmowa).
- Pełnej automatyzacji grafik „od A do Z” na start — koszt tokenów (setki mln/film) i ryzyko przeładowania.
- Ciężkiego renderu 4K na VPS — serwer ma 4 CPU / 7 GB RAM bez GPU i obsługuje fabrykę EA (n8n);
  render powinien iść na Twoim komputerze lub w nocy z limitem.

## Stan techniczny VPS (2026-10-29)
4 vCPU, 7 GB RAM (ok. 5 GB zajęte), brak GPU, **brak FFmpeg** (do instalacji), Node 24 (HyperFrames OK),
brak Chrome (potrzebny do HyperFrames).
