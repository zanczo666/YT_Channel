# B3 — przesył nagrań: telefon i komputer → `inbox/`

_Wersja 1.0 — 2026-11-03. Zbudowane i sprawdzone na `claudecore`._

Nagranie ma trafiać na serwer samo, bez `scp` i bez chmury. Robi to **Syncthing** po **tailnecie**
(Tailscale jest już na wszystkich urządzeniach), a kompletne pliki przenosi do `inbox/` skrypt
`scripts/odbierz.py` wołany z timera co minutę.

```
telefon  ──┐                    ~/sync/telefon  ──┐
           ├─ Tailscale ─► claudecore ─ Syncthing ─┤ odbierz.py (timer 1 min) ─► ~/inbox ─► pipeline
komputer ──┘                    ~/sync/komputer ──┘
```

## Dlaczego tak

- **Tailscale, nie publiczny port.** Syncthing nasłuchuje wyłącznie na `100.69.173.24` (adres tailnetu).
  Odkrywanie globalne, relaye i NAT-PMP są **wyłączone** — ruch nie wychodzi poza tailnet, a na publicznym
  interfejsie nie ma czego pukać. `ufw` i tak przepuszcza tylko `tailscale0`, więc to druga warstwa.
- **Osobne foldery `~/sync/...` zamiast synchronizowania `inbox/` wprost.** Pipeline czyta i przerabia
  `inbox/`; gdyby to był folder Syncthinga, każda operacja montażu byłaby dla niego „lokalną zmianą”
  do pogodzenia. Tak granica jest czysta: Syncthing pisze tylko do `~/sync`, pipeline czyta tylko `inbox/`.
- **Foldery na serwerze są „tylko odbiór” (receive only).** Nic, co stanie się na serwerze, nie wróci
  do telefonu — żadne porządki po stronie serwera nie usuną Ci nagrania z galerii.
- **Twarde łącze, nie kopia.** `odbierz.py` robi `os.link`: natychmiast i bez drugiej kopii 200 MB.
  Gdy usuniesz nagranie w telefonie, zniknie z `~/sync`, ale **łącze w `inbox/` zostaje** — materiał
  źródłowy nie przepada przez sprzątanie galerii.
- **Warunek kompletności to niezmienny rozmiar przez 45 s.** Syncthing zmienia nazwę z `.tmp` na docelową
  po komplecie, więc sam przesył jest bezpieczny. Ale OBS na komputerze pisze **prosto do folderu
  synchronizowanego**, więc Syncthing wysyła plik, który wciąż rośnie — po stronie serwera widać wtedy
  niepełne nagranie pod docelową nazwą. Dlatego liczy się stabilność, nie sama nazwa.

## Stan na serwerze (gotowe)

| Rzecz | Wartość |
|---|---|
| ID urządzenia `claudecore` | `STMWVBE-JL5RCRV-KCYPS35-B53Z6P3-O5FZVY7-SMT5AOX-SIDJ6TX-7OHE2QJ` |
| Adres do wpisania na kliencie | `tcp://100.69.173.24:22000` |
| Panel Syncthinga | `http://100.69.173.24:8384` (tylko z tailnetu), użytkownik `claude` |
| Hasło do panelu | `~/.config/yt_channel/syncthing_gui_password` (chmod 600, nigdy nie wypisujemy) |
| Folder dla telefonu | ID `yt-telefon`, `~/sync/telefon`, receive only |
| Folder dla komputera | ID `yt-komputer`, `~/sync/komputer`, receive only |
| Usługa | `systemctl --user status syncthing` (restart automatyczny, czeka na `tailscale0`) |
| Odbiór do `inbox/` | `systemctl --user list-timers odbierz-nagrania.timer`, log: `~/.local/state/yt_channel/odbierz.log` |

## Telefon (Android)

1. **Tailscale musi być włączony** (VPN aktywny) — bez niego adres `100.69.173.24` nie istnieje.
   Telefon jest już w tailnecie jako `redmi-note-14-pro-5g`. Warto ustawić „always on” i wyjąć
   Tailscale oraz Syncthinga z optymalizacji baterii — inaczej Android je uśpi i nagranie pojedzie
   dopiero po odblokowaniu telefonu.
2. Zainstaluj **Syncthing-Fork** (Catfriend1) z F-Droida albo Google Play. Oficjalna aplikacja
   „Syncthing” została wycofana przez autorów — fork jest tym utrzymywanym.
3. Dodaj urządzenie `claudecore`: ID i adres `tcp://100.69.173.24:22000` z tabeli wyżej.
   Adres trzeba wpisać ręcznie zamiast `dynamic` — odkrywanie globalne jest wyłączone po obu stronach.
4. Serwer ma już udostępniony folder `yt-telefon`, więc w telefonie pojawi się propozycja do przyjęcia.
   Wskaż **`/storage/emulated/0/DCIM/Camera`** i ustaw typ **Send Only**.

### Dlaczego folder kamery, a nie osobny katalog

Aparat w HyperOS (Redmi Note 14 Pro+) **nie pozwala zmienić katalogu zapisu** — Android narzuca
`DCIM/Camera`. Alternatywy są gorsze: inna aplikacja aparatu (np. Open Camera) umie wskazać folder,
ale traci przetwarzanie obrazu Xiaomi, a dla gadającej głowy jakość obrazu jest ważniejsza niż wygoda
ścieżki; reguła w Tasker/MacroDroid przenosząca pliki to kolejny element, który może się zepsuć po cichu.
Dlatego synchronizujemy folder kamery, a **bramką jest nazwa pliku**.

**Wzorce ignorowania w telefonie** (ustawienia folderu → Ignoruj wzorce):

```
.pending-*
.trashed-*
!yt*.mp4
!yt*.MP4
!YT*.mp4
!YT*.MP4
*
```

Pierwszy pasujący wzorzec wygrywa. Z folderu wychodzą **wyłącznie pliki `yt*.mp4`** — zdjęcia, zrzuty
ekranu i wcześniejsze filmy `VID_…` zostają w telefonie. Cztery warianty wielkości liter, bo wzorce
Syncthinga są domyślnie wrażliwe na wielkość znaków.

**Jak się tego używa:** nagrywasz normalnie aparatem, potem w galerii albo menedżerze plików zmieniasz
nazwę na `yt-<cokolwiek>.mp4`. Ta zmiana nazwy **jest** decyzją „to idzie na kanał” — nic nie wyjeżdża
z telefonu przypadkiem, a system nie musi zgadywać z długości ani daty, co jest materiałem.

`.pending-…` to nagranie w trakcie zapisu (MediaStore nadaje docelową nazwę dopiero po zamknięciu pliku),
`.trashed-…` to kosz galerii. Zostają na liście jako zabezpieczenie: gdyby nazwa zmieniła się jeszcze
w trakcie zapisu, niedokończony plik i tak nie pojedzie.

**Próg długości na serwerze jest wyłączony** (`MIN_CZAS_S = 0`). Miał sens, dopóki na serwer trafiał
cały folder kamery i trzeba było odsiewać przypadkowe klipy; przy bramce w nazwie odrzucałby świadomie
nagrany krótki materiał. Zostaje jako opcja:

```bash
python3 ~/projects/YT_Channel/scripts/odbierz.py --min-czas 20
```

5. Syncthing-Fork ma osobny przełącznik „Run on mobile data”. Nagranie to ~200 MB, więc raczej tylko Wi-Fi.

## Komputer (Windows)

1. Tailscale włączony (laptop jest w tailnecie jako `laptop-is8g390a`).
2. Zainstaluj **SyncTrayzor** (Syncthing z ikoną w zasobniku i autostartem) albo samą binarkę Syncthinga.
3. Dodaj urządzenie: ID `claudecore` jak w tabeli wyżej, adres `tcp://100.69.173.24:22000`.
4. Prześlij mi **Device ID** komputera — udostępniam folder `yt-komputer`.
5. Przyjmując folder wskaż katalog, do którego **OBS zapisuje nagrania**, i ustaw typ **Send Only**.
   Nic więcej: kończysz nagranie w OBS, plik dojeżdża na serwer, minutę po tym, jak przestanie rosnąć,
   ląduje w `inbox/`.

Sprawdzenie łączności z komputera:

```powershell
Test-NetConnection -ComputerName 100.69.173.24 -Port 22000
```

## Sprawdzenie, że zadziałało

Na serwerze:

```bash
tail -n 20 ~/.local/state/yt_channel/odbierz.log
ls -lh ~/inbox/
```

## Co zostaje ręcznie

- **Dodanie nowego urządzenia** — jego Device ID musi ktoś wpisać na serwerze (ja, przez API Syncthinga).
  Świadomie: `autoAcceptFolders` jest wyłączone, więc obce urządzenie nie dostanie nic samo.
- **Porządki w `~/sync`** — pliki usuwasz w telefonie/na komputerze, serwer tylko podąża.
  W `inbox/` zostają twarde łącza; czyści je sprzątanie pipeline'u po zakończonym filmie.
