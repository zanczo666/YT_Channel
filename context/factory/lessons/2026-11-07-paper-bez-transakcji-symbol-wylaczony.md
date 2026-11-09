---
typ: lesson
data_zdarzenia: 2026-11-07
etap: 12_Paper_Trading
publish_after: 2026-11-28
---
# Dwa tygodnie paper tradingu bez jednej transakcji — i żaden alarm
## Co się wydarzyło
Pierwsza strategia, która przeszła test w Pythonie i parytet w testerze MT5, od dwóch tygodni działała na koncie demo. Dashboard pokazywał żywy terminal, wykres z EA i zero otwartych pozycji, więc wyglądało to na zwykły brak sygnałów.
W dzienniku EA były cztery sygnały wejścia i cztery odrzucone zlecenia z kodem „Trade disabled”.
## Przyczyna
Na serwerze demo cała grupa indeksów ma wyłączony handel. Notowania płyną, świece się rysują, a zlecenie zawsze zostaje odrzucone. Tester strategii nie sprawdza trybu handlu symbolu, więc wszystkie wcześniejsze bramki to przepuściły.
EA po odrzuceniu nie ponawiał wejścia, a eksport transakcji widzi tylko zlecenia wykonane, nie odrzucone.
## Zasada ogólna
Brak transakcji to też wynik, który trzeba wyjaśnić. Monitoring liczący tylko wykonane zlecenia nie odróżni strategii bez sygnałów od strategii, której sygnały odbija broker.
## Jak wykryć u siebie
Przed startem na koncie sprawdź tryb handlu i sesje symbolu (w MQL5: `SYMBOL_TRADE_MODE`, `SymbolInfoSessionTrade`). Codziennie zbieraj z dziennika EA odrzucone zlecenia i zapisuj je poza terminalem, bo terminal po kilku dniach kasuje stare dzienniki.
Porównaj dzień paperu z silnikiem backtestu uruchomionym na tych samych świecach. U nas silnik wskazał wejścia dokładnie w chwilach odrzuconych zleceń.
## Liczby
- 14 dni na koncie demo, 0 transakcji, 4 odrzucone zlecenia.
- Silnik na świecach brokera z tego okresu: 2 wejścia, oba w minucie odrzuconego zlecenia.
- Symbole z wyłączonym handlem w grupie indeksów: 26 z 26.
## Można pokazać
- Dashboard „wszystko zielone” obok linijek dziennika z odrzuceniami.
- Raport dzienny Paper Check z alertem trybu handlu symbolu.
## Nie pokazywać
- Reguł i parametrów strategii, kodu EA, numeru konta, adresów serwerów.
