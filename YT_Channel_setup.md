# YT_Channel — instrukcja uruchomienia (Hetzner VPS)

Cel: trzeci projekt Claude Code, który **czyta** MQL5_Freelancer (tylko `codebase/`) i N8N_EA_System, **nigdy ich nie zmienia**, dostaje świeży kontekst automatycznie i działa jako instancja Remote Control jak pozostałe dwa projekty.

Wszystkie polecenia wykonujesz jako ten sam użytkownik, pod którym działają już `claude-rc` dla pozostałych projektów.

---

## Krok 0. Ustal ścieżki i sprawdź stan

```bash
echo $HOME                      # np. /home/zanczo — będzie potrzebne w settings.json
ls ~/projects                   # powinny być: MQL5_Freelancer  N8N_EA_System  YT_Channel
claude --version
git -C ~/projects/MQL5_Freelancer branch --show-current
git -C ~/projects/N8N_EA_System branch --show-current
```

**Po co:** w plikach ustawień Claude Code nie działa `$HOME`, więc ścieżki wpisujesz dosłownie. Jeśli główną gałęzią nie jest `main`, zmienisz to w skrypcie w kroku 6.

W dalszej części `/home/UZYTKOWNIK` zamień na wynik `echo $HOME`. Jeśli projekty nie leżą w `~/projects`, popraw też to.

---

## Krok 1. Repozytorium gita dla YT_Channel

```bash
cd ~/projects/YT_Channel
git init -b main
mkdir -p .claude/commands scripts context/feed context/tools content/ideas content/scripts
cat > .gitignore <<'EOF'
.claude/settings.local.json
CLAUDE.local.md
context/.last_sync
context/.seen_commits
.worktrees/
__pycache__/
EOF
```

**Po co:**
- Remote Control z `--spawn worktree` tworzy osobny worktree dla każdej sesji, więc **wymaga repozytorium gita z co najmniej jednym commitem**. Bez tego instancja nie wystartuje poprawnie.
- `.claude/settings.local.json` jest ignorowany, bo tam Claude Code zapisuje Twoje lokalne zgody (np. z panelu `/sandbox`). To nie powinno trafić do repo.
- `context/.last_sync` i `.seen_commits` to stan skryptu synchronizacji. Jest lokalny dla serwera.

Struktura docelowa:

```
YT_Channel/
├── CLAUDE.md                  # krótkie instrukcje projektu
├── .claude/
│   ├── settings.json          # uprawnienia + sandbox (commitowane)
│   └── commands/
│       └── pomysly.md         # /pomysly — propozycje filmów z feedu
├── scripts/
│   └── sync_context.py        # zbiera kontekst z dwóch projektów (bez LLM)
├── context/
│   ├── feed/2026-W38.md       # tygodniowe digesty zdarzeń (commitowane)
│   └── tools/<Narzędzie>.md   # kopie kart VIDEO.md z codebase
└── content/
    ├── ideas/                 # pomysły na filmy
    └── scripts/               # scenariusze
```

Commit robisz na końcu kroku 6, kiedy wszystkie pliki będą na miejscu.

---

## Krok 2. Przygotowanie projektów źródłowych (jednorazowo)

To jedyne zmiany w istniejących projektach. Wprowadzasz je **z ich własnych sesji** Claude Code (albo ręcznie), nie z YT_Channel, bo YT_Channel będzie miał zapis tam zablokowany.

### 2a. `docs/OVERVIEW.md` w obu projektach

W sesji każdego projektu wydaj polecenie:

> Utwórz `docs/OVERVIEW.md` (max 60 linii): czym jest projekt, architektura w punktach, co już działa, co jest w toku. Bez sekretów, kluczy, adresów IP, nazw klientów. Zacommituj.

**Po co:** to jedyny statyczny kontekst, który YT_Channel ładuje przy starcie (krok 3). Krótki plik oznacza mało tokenów w każdej sesji.

### 2b. Karta `VIDEO.md` przy każdym narzędziu w MQL5_Freelancer

Każde narzędzie w `codebase/<NazwaNarzędzia>/` dostaje plik `VIDEO.md`:

```markdown
# NazwaNarzędzia
Problem: jaki ból tradera to rozwiązuje (jedno zdanie)
Dla kogo: początkujący / zaawansowany / programista MQL5
Demo: co pokazać na wykresie w 60 sekund
Przed/po: jak wyglądało to bez narzędzia
Haczyki: nieoczywiste ustawienia, typowe błędy
Link: adres publikacji w Codebase
```

Dopisz jedną linię do CLAUDE.md projektu MQL5_Freelancer, żeby jego sesje o tym pamiętały:

```markdown
- Przy publikacji narzędzia w `codebase/` utwórz lub zaktualizuj `codebase/<narzędzie>/VIDEO.md` według szablonu (problem, dla kogo, demo, przed/po, haczyki, link).
```

**Konsekwencja:** skrypt synchronizacji czyta **wyłącznie** `codebase/`. Commity dotyczące klientów w ogóle nie trafiają do feedu, bo są filtrowane po ścieżce na poziomie gita, a nie przez prompt.

### 2c. Trailer `Content: yes` w N8N_EA_System

Dopisz do CLAUDE.md projektu N8N_EA_System:

```markdown
- Gdy commit dotyczy czegoś wartego pokazania publicznie (wynik researchu, odrzucona strategia z lekcją, eksperyment TFT, zmiana architektury), dodaj na końcu wiadomości commita trailer `Content: yes`, a w treści commita jedną linię "Lekcja: ...". Nie opisuj w commicie pełnej logiki sprzedawanych strategii.
```

Ręcznie to wygląda tak:

```bash
git commit -m "Walk-forward: 37/40 strategii odrzuconych" -m "Lekcja: overfitting na H1 przy <2 lat danych" -m "Content: yes"
```

**Po co:** fabryka generuje dużo commitów technicznych (refaktory, poprawki n8n), które nie są materiałem na film. Trailer to ręczny (lub przez Claude) wybór, co jest ciekawe.

---

## Krok 3. `CLAUDE.md` projektu YT_Channel

```bash
cat > ~/projects/YT_Channel/CLAUDE.md <<'EOF'
# YT_Channel

Kanał YouTube o darmowych narzędziach MQL5 (Codebase) oraz o budowie fabryki EA (research, backtesty, TFT).
Cel: dobry, merytoryczny content; widz sam trafia na profil mql5.com.

## Kontekst projektów źródłowych (tylko odczyt)
- Freelance, darmowe narzędzia: @/home/UZYTKOWNIK/projects/MQL5_Freelancer/docs/OVERVIEW.md
- Fabryka EA: @/home/UZYTKOWNIK/projects/N8N_EA_System/docs/OVERVIEW.md
- Świeże zdarzenia: `context/feed/` (najnowszy plik tygodniowy). Karty narzędzi: `context/tools/`.
- Do katalogów projektów źródłowych sięgaj tylko po konkretny plik potrzebny do filmu (np. kod do pokazania na ekranie).

## Granice treści
- Nigdy nie wspominaj klientów, zleceń ani prac wykonanych dla kogokolwiek.
- Nie ujawniaj pełnej logiki strategii przeznaczonych do sprzedaży: pokazuj proces, nie przepis.
- Wyniki backtestów zawsze z zastrzeżeniem, że to nie porada inwestycyjna, a wyniki historyczne nie gwarantują przyszłych.

## Konwencje
- Pomysły: `content/ideas/RRRR-MM-DD-slug.md`. Scenariusze: `content/scripts/slug.md`.
- Język treści: polski (chyba że zaznaczę inaczej).
EOF
```

**Po co i konsekwencje:**
- Linie `@/ścieżka` to **importy**. Pliki są wklejane do kontekstu przy starcie każdej sesji. Dlatego OVERVIEW.md ma być krótki.
- Import spoza katalogu projektu jest „zewnętrzny”. Przy pierwszym uruchomieniu Claude Code pokaże okno zatwierdzenia z listą plików. **Jeśli odrzucisz, importy zostaną wyłączone i okno już się nie pojawi**, więc w kroku 7 zatwierdź je świadomie.
- Nie wpisuj tu pełnego CLAUDE.md projektów źródłowych. Ich instrukcje (pipeline, n8n, MQL5) nie powinny sterować sesją piszącą scenariusze.
- „Granice treści” to wskazówki, nie twarda blokada. Twardą granicę dają ustawienia (krok 4) i filtr ścieżek w skrypcie (krok 6).

---

## Krok 4. `.claude/settings.json` — uprawnienia i sandbox

```bash
cat > ~/projects/YT_Channel/.claude/settings.json <<'EOF'
{
  "permissions": {
    "defaultMode": "acceptEdits",
    "additionalDirectories": [
      "/home/UZYTKOWNIK/projects/MQL5_Freelancer",
      "/home/UZYTKOWNIK/projects/N8N_EA_System"
    ],
    "allow": [
      "Bash(python3 scripts/sync_context.py)",
      "Bash(git -C /home/UZYTKOWNIK/projects/MQL5_Freelancer log *)",
      "Bash(git -C /home/UZYTKOWNIK/projects/N8N_EA_System log *)",
      "Bash(git -C /home/UZYTKOWNIK/projects/MQL5_Freelancer show *)",
      "Bash(git -C /home/UZYTKOWNIK/projects/N8N_EA_System show *)"
    ],
    "deny": [
      "Edit(//home/UZYTKOWNIK/projects/MQL5_Freelancer/**)",
      "Edit(//home/UZYTKOWNIK/projects/N8N_EA_System/**)",
      "Read(//home/UZYTKOWNIK/projects/MQL5_Freelancer/**)",
      "Read(//home/UZYTKOWNIK/projects/**/.env)",
      "Read(//home/UZYTKOWNIK/projects/**/.env.*)"
    ],
    "ask": []
  },
  "sandbox": {
    "enabled": true,
    "failIfUnavailable": true,
    "allowUnsandboxedCommands": false,
    "filesystem": {
      "denyRead": [
        "/home/UZYTKOWNIK/projects/MQL5_Freelancer/clients",
        "/home/UZYTKOWNIK/projects/MQL5_Freelancer/jobs"
      ]
    }
  }
}
EOF
```

> **Uwaga do `Read(...MQL5_Freelancer/**)` w `deny`:** ta reguła blokuje odczyt **całego** repo freelance przez narzędzia Claude. To najbezpieczniejszy wariant, bo YT_Channel i tak dostaje z freelance tylko to, co skrypt skopiuje do `context/tools/`. Jeśli chcesz, żeby Claude mógł czytać kod narzędzi do pokazania na ekranie, zamień tę jedną regułę na blokady konkretnych katalogów z danymi klientów (np. `clients/**`, `jobs/**`, i co tam jeszcze masz). Nazwy `clients` i `jobs` w sekcji `sandbox` to przykłady; wpisz faktyczne katalogi z danymi klientów.

### Co robi każde ustawienie i jakie ma konsekwencje

| Ustawienie | Co robi | Konsekwencja |
|---|---|---|
| `defaultMode: acceptEdits` | Claude edytuje pliki w YT_Channel bez pytania; polecenia spoza `allow` wymagają zgody. | Wygodne przy pisaniu scenariuszy. **Nie używaj tu `bypassPermissions`**: ten projekt nie ma powodu działać bez nadzoru. |
| `additionalDirectories` | Dołącza oba projekty jako dodatkowe katalogi robocze. | Pliki w nich są czytelne bez pytania. Edycja podlegałaby trybowi uprawnień, dlatego niżej jest `deny`. **CLAUDE.md z tych katalogów nie jest ładowany**, dopóki nie ustawisz `CLAUDE_CODE_ADDITIONAL_DIRECTORIES_CLAUDE_MD=1`. Nie ustawiaj tej zmiennej. |
| `allow: Bash(...)` | Polecenia wykonywane bez pytania: skrypt synchronizacji oraz `git log` / `git show` na projektach źródłowych. | Tylko odczyt historii gita. `git -C ... commit` czy `push` nie pasują do reguł, więc wymagałyby zgody (a i tak blokuje je sandbox). |
| `deny: Edit(//...)` | Blokuje edycję w obu projektach wszystkimi wbudowanymi narzędziami edycji (Edit, Write itd.). | `deny` ma pierwszeństwo przed `allow` i przed `additionalDirectories`. **Podwójny ukośnik `//` oznacza ścieżkę bezwzględną.** Pojedynczy `/` byłby liczony względem projektu i reguła by nie zadziałała. |
| `deny: Read(.env)` | Claude nie przeczyta plików z sekretami. | Dotyczy narzędzi Read/Grep/Glob. Polecenia Bash obsługuje sandbox (niżej). |
| `sandbox.enabled` | Polecenia Bash działają w izolacji bubblewrap. Domyślnie **zapis tylko w katalogu roboczym** (YT_Channel) i katalogu tymczasowym. | To jest **twarda, systemowa** blokada. Reguły `deny` działają na narzędzia Claude, ale nie na procesy uruchomione z Basha (np. skrypt Pythona, który sam otwiera pliki). Sandbox zamyka tę lukę: `echo x > ~/projects/N8N_EA_System/plik` zostanie odrzucone przez system. |
| `failIfUnavailable: true` | Jeśli sandbox nie wystartuje, polecenia Bash kończą się błędem. | Bez tego Claude Code tylko ostrzega i uruchamia polecenia **bez izolacji**. Przy headless to ostrzeżenie łatwo przeoczyć. |
| `allowUnsandboxedCommands: false` | Wyłącza „furtkę”, przez którą Claude może ponowić polecenie poza sandboxem. | Wszystko musi działać w sandboxie. Jeśli coś tego wymaga, dostaniesz błąd zamiast prośby o zgodę. |
| `filesystem.denyRead` | Blokuje procesom Bash odczyt wskazanych katalogów. | Uzupełnienie `deny: Read` na poziomie systemu. |

Sieć w sandboxie: przy pierwszej próbie połączenia z nową domeną Claude Code poprosi o zgodę (w Remote Control prośba przyjdzie na telefon). Do działania projektu sieć z Basha nie jest potrzebna, bo `git fetch` robi timer poza Claude (krok 6).

---

## Krok 5. Zależności sandboxa

```bash
sudo apt update && sudo apt install -y bubblewrap socat
bwrap --version
```

**Po co:** na Linuksie sandbox Claude Code używa bubblewrap. Bez tego pakietu przy `failIfUnavailable: true` każde polecenie Bash w YT_Channel się nie powiedzie. To zamierzone.

Jeśli `bwrap` zgłasza błąd przestrzeni nazw użytkownika:

```bash
sysctl kernel.unprivileged_userns_clone        # na Debianie powinno być 1
sysctl kernel.apparmor_restrict_unprivileged_userns   # na Ubuntu 24.04 może blokować
```

Na Ubuntu 24.04 ograniczenie AppArmor bywa przyczyną. Rozwiązaniem jest profil AppArmor dla `bwrap`, a nie globalne wyłączanie ograniczenia.

---

## Krok 6. Skrypt synchronizacji i timer

### 6a. Skrypt

Zapisz dostarczony plik `sync_context.py` jako `~/projects/YT_Channel/scripts/sync_context.py`.

Co robi:
- Z **MQL5_Freelancer** bierze tylko commity dotykające `codebase/` i kopiuje wszystkie karty `codebase/*/VIDEO.md` do `context/tools/`.
- Z **N8N_EA_System** bierze tylko commity z trailerem `Content: yes`.
- Czyta z gałęzi `main` (`git log main`, `git show main:plik`), **nie z katalogu roboczego**. To ważne, bo instancje z `--spawn worktree` pracują w osobnych worktree, a katalog główny może być nieaktualny.
- Dopisuje wynik do `context/feed/RRRR-Www.md`, pamięta ostatnią synchronizację i już zebrane commity (bez duplikatów).
- Nie używa LLM, więc nie kosztuje tokenów.

Konfiguracja jest na górze pliku (`SOURCES`): gałąź (`ref`), filtrowane ścieżki (`paths`), tryb trailera (`only_flagged`).

Jeśli projekty trafiają do `main` dopiero przez GitHub (a nie lokalny merge), zmień `ref` na `origin/main` i dodaj fetch w usłudze (6b).

Test ręczny:

```bash
cd ~/projects/YT_Channel
chmod +x scripts/sync_context.py
python3 scripts/sync_context.py
ls context/feed context/tools
```

Pierwsze uruchomienie zbiera ostatnie 30 dni.

### 6b. Timer systemd (co 6 godzin)

```bash
mkdir -p ~/.config/systemd/user
cat > ~/.config/systemd/user/yt-sync.service <<'EOF'
[Unit]
Description=YT_Channel: synchronizacja kontekstu z projektów źródłowych

[Service]
Type=oneshot
WorkingDirectory=%h/projects/YT_Channel
# Odkomentuj, jeśli w SOURCES używasz origin/main:
# ExecStartPre=/usr/bin/git -C %h/projects/MQL5_Freelancer fetch --quiet origin
# ExecStartPre=/usr/bin/git -C %h/projects/N8N_EA_System fetch --quiet origin
ExecStart=/usr/bin/python3 %h/projects/YT_Channel/scripts/sync_context.py
EOF

cat > ~/.config/systemd/user/yt-sync.timer <<'EOF'
[Unit]
Description=YT_Channel: synchronizacja co 6h

[Timer]
OnBootSec=10min
OnUnitActiveSec=6h
Persistent=true

[Install]
WantedBy=timers.target
EOF

systemctl --user daemon-reload
systemctl --user enable --now yt-sync.timer
systemctl --user list-timers | grep yt-sync
journalctl --user -u yt-sync.service -n 20
```

**Dlaczego timer, a nie n8n albo Hermes:** to zwykły skrypt bez LLM. Timer systemd nie ma zależności, działa po restarcie serwera (`Persistent=true` nadrabia przegapione uruchomienia) i jest w tym samym miejscu co reszta Twoich usług `--user`. Do n8n warto go przenieść dopiero, gdy dojdą źródła z PostgreSQL lub Notion.

### 6c. Komenda `/pomysly`

```bash
cat > ~/projects/YT_Channel/.claude/commands/pomysly.md <<'EOF'
---
description: Propozycje filmów na podstawie najnowszego feedu i kart narzędzi
---
Przeczytaj najnowszy plik w `context/feed/` oraz karty w `context/tools/`, które się w nim pojawiają.
Zaproponuj 3–5 tematów filmów. Dla każdego: tytuł roboczy, filar (narzędzie / research / build in public), hak na pierwsze 15 sekund, co pokazać na ekranie, czego NIE pokazywać.
Zapisz wynik do `content/ideas/` z dzisiejszą datą w nazwie pliku.
$ARGUMENTS
EOF
```

### 6d. Pierwszy commit

```bash
cd ~/projects/YT_Channel
git add -A
git commit -m "YT_Channel: szkielet, uprawnienia, sandbox, synchronizacja kontekstu"
```

Na GitHubie utwórz **prywatne** repo i podłącz je (`git remote add origin ...`, `git push -u origin main`). Feed zawiera nazwy commitów z fabryki, które nie muszą być publiczne.

---

## Krok 7. Pierwsze uruchomienie interaktywne (obowiązkowe)

Instancja Remote Control nie przejdzie jednorazowych okien dialogowych sama, dlatego pierwszy raz uruchamiasz Claude ręcznie w terminalu (przez SSH):

```bash
cd ~/projects/YT_Channel
claude
```

Po kolei:
1. **Okno zaufania do folderu** → zaakceptuj. Bez tego Remote Control w tym katalogu nie zadziała, a hooki i ustawienia projektu nie zostaną wczytane.
2. **Okno zewnętrznych importów** (dwa pliki OVERVIEW.md) → zaakceptuj.
3. Sprawdzenia w sesji:
   - `/context` → w sekcji Memory files powinny być `CLAUDE.md` projektu i oba `OVERVIEW.md`. **Nie** powinno być CLAUDE.md projektów źródłowych.
   - `/permissions` → widać reguły `allow` / `deny` z kroku 4.
   - `/sandbox` → sandbox włączony.
4. Testy granic (wpisz w sesji jako polecenia dla Claude):

| Test | Oczekiwany wynik |
|---|---|
| „Pokaż ostatnie 5 commitów N8N_EA_System przez git log” | Działa bez pytania. |
| „Przeczytaj docs/OVERVIEW.md z N8N_EA_System” | Działa. |
| „Dopisz linię do docs/OVERVIEW.md w N8N_EA_System” | **Odmowa** (reguła deny). |
| „Uruchom `touch ~/projects/N8N_EA_System/test.txt`” | **Błąd** (sandbox: zapis poza katalogiem roboczym). |
| „Przeczytaj dowolny plik z MQL5_Freelancer” | **Odmowa** (przy wariancie z pełną blokadą odczytu). |
| „/pomysly” | Powstaje plik w `content/ideas/`. |

Jeśli któryś test blokujący **przeszedł**, zatrzymaj się i sprawdź ścieżki w `settings.json` (najczęstszy błąd: pojedynczy `/` zamiast `//` albo literówka w nazwie użytkownika).

Wyjdź z sesji (`/exit`) i posprzątaj ewentualny plik testowy.

---

## Krok 8. Instancja Remote Control z tego samego szablonu

### 8a. Sprawdź szablon, zanim go użyjesz

```bash
systemctl --user cat claude-rc@.service
```

Zwróć uwagę na trzy rzeczy:

1. **Jak `%i` przechodzi w katalog.** Szukaj `WorkingDirectory=`. Jeśli jest np. `WorkingDirectory=%h/projects/%i`, nazwa instancji musi być dokładnie `YT_Channel`.
2. **Flagi w `ExecStart`.** Jeśli szablon ma `--permission-mode bypassPermissions` albo `--dangerously-skip-permissions`, **nie chcesz tego dla YT_Channel** (patrz 8b).
3. **`Environment=`.** Jeśli szablon ustawia `CLAUDE_CODE_ADDITIONAL_DIRECTORIES_CLAUDE_MD=1`, w YT_Channel ładowałyby się CLAUDE.md projektów źródłowych. Nadpisz to w 8b.

### 8b. Nadpisanie tylko dla tej instancji (jeśli potrzebne)

```bash
systemctl --user edit claude-rc@YT_Channel.service
```

W edytorze wpisz tylko to, co chcesz zmienić, np.:

```ini
[Service]
Environment=CLAUDE_CODE_ADDITIONAL_DIRECTORIES_CLAUDE_MD=0
ExecStart=
ExecStart=/ŚCIEŻKA/DO/claude remote-control --name "YT_Channel" --spawn worktree
```

Pusta linia `ExecStart=` jest wymagana: czyści oryginalną komendę z szablonu przed podaniem nowej. Ścieżkę do `claude` i resztę flag skopiuj z szablonu, usuwając tylko to, czego nie chcesz. Drop-in trafia do `~/.config/systemd/user/claude-rc@YT_Channel.service.d/override.conf` i **nie zmienia** pozostałych instancji.

Jeśli szablon nie ma żadnego z tych trzech problemów, pomiń 8b.

### 8c. Uruchomienie

```bash
systemctl --user daemon-reload
systemctl --user enable --now claude-rc@YT_Channel.service
systemctl --user status claude-rc@YT_Channel.service
journalctl --user -u claude-rc@YT_Channel.service -n 50 -f
```

`enable` sprawia, że instancja wstaje po restarcie serwera (wymaga włączonego lingera, który masz już dla pozostałych: `loginctl show-user $USER | grep Linger` → `Linger=yes`).

Jeśli masz slice `app-claude-rc.slice` przypisany w szablonie, nowa instancja trafi do niego automatycznie i będzie dzielić z pozostałymi limity zasobów:

```bash
systemctl --user status app-claude-rc.slice
```

### 8d. Połączenie

Otwórz aplikację Claude (telefon) albo claude.ai/code. Na liście sesji Remote Control pojawi się `YT_Channel`. Nowa sesja dostanie własny worktree.

**Konsekwencja `--spawn worktree` dla tego projektu:** scenariusze tworzone w sesji lądują w worktree na osobnej gałęzi. Żeby trafiły do `main`, sesja musi je zacommitować i zmergować (albo robisz to ręcznie). Timer synchronizacji pisze natomiast do katalogu głównego na `main`. Jeśli wolisz prostszy model dla projektu treściowego (jedna sesja naraz, wszystko na `main`), usuń w 8b `--spawn worktree`.

---

## Krok 9. Lista kontrolna „działa”

- [ ] `git -C ~/projects/YT_Channel log --oneline` pokazuje commit.
- [ ] `systemctl --user list-timers | grep yt-sync` pokazuje najbliższe uruchomienie.
- [ ] `context/feed/` ma plik tygodniowy, `context/tools/` ma karty (o ile w `codebase/` są już `VIDEO.md`).
- [ ] `/context` w sesji: CLAUDE.md projektu + 2× OVERVIEW.md, bez CLAUDE.md źródeł.
- [ ] Testy blokujące z kroku 7 kończą się odmową lub błędem.
- [ ] `systemctl --user status claude-rc@YT_Channel.service` → `active (running)`.
- [ ] Sesja YT_Channel widoczna w aplikacji Claude.
- [ ] `/pomysly` tworzy plik w `content/ideas/`.

---

## Rozwiązywanie problemów

| Objaw | Przyczyna | Rozwiązanie |
|---|---|---|
| OVERVIEW.md nie widać w `/context` | Odrzucone okno importów albo zła ścieżka. | Popraw ścieżkę w CLAUDE.md. Po odrzuceniu okno nie wraca, więc sprawdź ustawienia zgód projektu w `/permissions` lub `/memory`. |
| Każde polecenie Bash kończy się błędem `bwrap` | Brak bubblewrap albo ograniczenie przestrzeni nazw. | Krok 5. |
| Claude edytował plik w projekcie źródłowym | Reguła `deny` z pojedynczym `/` lub zła nazwa użytkownika. | Popraw na `//home/...` i sprawdź w `/permissions`. |
| Instancja RC restartuje się w pętli | Brak zaakceptowanego zaufania do folderu lub brak commita w repo. | Krok 7 i 6d. |
| Feed pusty mimo nowych commitów | Commity są na innej gałęzi niż `ref` albo brak trailera `Content: yes`. | `git -C <repo> log --all --oneline -5`; popraw `ref` w `SOURCES`. |
| Duplikaty w feedzie | Usunięty `context/.seen_commits`. | Plik odtworzy się sam; usuń ręcznie powtórzone linie. |

---

## Źródła (dokumentacja Claude Code)

- Pamięć, CLAUDE.md, importy, dodatkowe katalogi: https://code.claude.com/docs/en/memory
- Uprawnienia i składnia ścieżek: https://code.claude.com/docs/en/permissions
- Sandbox: https://code.claude.com/docs/en/sandboxing
- Remote Control: https://code.claude.com/docs/en/remote-control
