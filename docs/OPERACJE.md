# Obsługa pipeline'u

Jak działa automat i co trzeba uzupełnić, żeby ruszył w pełni. Architektura i statusy: `docs/PIPELINE.md`.

## Jak to działa na co dzień
1. `runner.py nowy <slug> --zrodlo <karta albo temat> --filar "<filar>"` — nowy film (albo wybór z cotygodniowych pomysłów).
2. Agent pisze scenariusz, kontrola zgodności go sprawdza, a Ty akceptujesz (✅ na Discordzie albo `runner.py akceptuj <slug>`).
3. Nagrywasz według `docs/RECORDING.md`, plik `yt_<slug>.mp4` sam trafia do `~/inbox/`.
4. Runner montuje na workerze wszystkie nagrane filmy naraz, robi QC, pakiet, shorts i wgrywa film prywatnie.
5. Ty oglądasz podgląd prywatny i akceptujesz; runner ustawia najbliższy wolny termin z kalendarza.
6. Po publikacji: shorts co 2 dni, analityka po 7 i 28 dniach, komentarze codziennie, newsletter co miesiąc.

## Polecenia
| Polecenie | Co robi |
|---|---|
| `python3 scripts/runner.py status` | stan wszystkich filmów |
| `python3 scripts/runner.py akceptuj <slug>` / `popraw <slug> --uwagi "…"` | decyzja na bramce bez Discorda |
| `python3 scripts/runner.py ustaw <slug> <STAN> [--yt-id ID] [--kolor czysty]` | ręczne przestawienie, np. po wgraniu w Studio albo z wyborem stylu kolorów |
| `python3 scripts/runner.py kalendarz` | odświeża `content/calendar.md` |
| `python3 scripts/worker.py snapshot list` | obrazy workera |
| `python3 scripts/komentarze.py odpowiedz <ID> "…"` | wysyła zaakceptowaną odpowiedź na komentarz |

## Do uzupełnienia przez właściciela
Bez tych kroków runner działa, ale zatrzymuje się na wiadomości „zrób ręcznie” zamiast robić to sam.

### Discord (G2)
1. Discord Developer Portal → New Application → Bot → skopiuj token. Uprawnienia bota: Send Messages, Attach Files,
   Add Reactions, Read Message History.
2. Zaproś bota na prywatny serwer, kanał `#produkcja`. W ustawieniach Discorda włącz tryb dewelopera i skopiuj ID kanału
   oraz swoje ID użytkownika.
3. Zapisz konfigurację bez wyświetlania tokenu:
```powershell
$t = Read-Host "Token bota"; $k = Read-Host "ID kanału"; $u = Read-Host "Twoje ID"
"{`"token`": `"$t`", `"kanal_id`": `"$k`", `"wlasciciel_id`": `"$u`"}" | ssh claudecore "umask 077 && cat > /home/claude/.config/yt_channel/discord.json"
Remove-Variable t
```
4. Test: `python3 scripts/discord.py test`.

### YouTube API (D3, E1, E2)
1. Google Cloud Console, projekt `yt-channel-research-513011`: włącz YouTube Data API v3 i YouTube Analytics API.
2. Ekran zgody OAuth (tryb testowy, Twoje konto jako użytkownik testowy), potem Credentials → OAuth client ID → Desktop app.
   Pobierz JSON.
3. Wgraj go na serwer:
```powershell
scp C:\Users\Radek\Downloads\client_secret_*.json claudecore:/home/claude/.config/yt_channel/youtube_oauth_client.json
ssh claudecore "chmod 600 /home/claude/.config/yt_channel/youtube_oauth_client.json"
```
4. Autoryzacja z tunelem i zalogowaniem na **konto marki kanału**:
```powershell
ssh -L 8765:localhost:8765 claudecore "cd /home/claude/projects/YT_Channel; python3 scripts/yt_api.py autoryzuj"
```
5. Test: `python3 scripts/yt_api.py sprawdz`, potem playlisty filarów: `python3 scripts/upload.py playlisty`.
6. Audyt API (D4): `docs/legal/privacy-youtube-api.md`. Do jego zakończenia filmy z API są prywatne.

W trybie testowym Google token odświeżania może wygasać po 7 dniach; wtedy powtórz krok 4 albo opublikuj aplikację
(ekran zgody → In production), co nie wymaga audytu dla własnego konta.

### Kanał (F1, F3, F5, F7)
- Konto marki, `@radoslawlubas`, weryfikacja telefonu, opis i grafiki z `docs/CHANNEL_SETUP.md` i `assets/brand/`.
- E-mail kontaktowy do `docs/CHANNEL_SETUP.md`.
- Strona: zdjąć przykładowe liczby (pamięć projektu), potem Methodology, Ledger i polityka.

## Timery (systemd użytkownika)
| Timer | Co | Kiedy |
|---|---|---|
| `odbierz-nagrania.timer` | odbiór nagrań z Syncthinga do `~/inbox/` | co minutę |
| `worker-reap.timer` | watchdog kosztów workera (58 min) | co minutę |
| `yt-runner.timer` | `runner.py tick` | co 15 min |

Wstrzymanie automatu: `systemctl --user stop yt-runner.timer`; wznowienie: `start`.
