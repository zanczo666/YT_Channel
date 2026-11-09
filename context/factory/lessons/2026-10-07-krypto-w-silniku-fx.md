---
typ: lesson
data_zdarzenia: 2026-10-07
etap: 03_Python_Backtest
commit: cf052a0
publish_after: 2026-10-28
---
# Bitcoin policzony jak para walutowa: koszty, rollover i brakujące weekendy
## Co się wydarzyło
7.10 przegląd nocnego backtestu strategii na BTCUSD pokazał, że silnik policzył ją profilem forex.
Wynik okazał się nieważny: zły model kosztów i brak ok. 29% świec. Silnik dostał osobną klasę instrumentów
krypto, a wynik tego przebiegu oznaczono do powtórki.
## Przyczyna
Rozpoznanie klasy instrumentu po kształcie symbolu: każdy 6-literowy symbol (EURUSD, BTCUSD) trafiał do forex —
z kosztem i swapem forex oraz wielkością punktu 0,00001. Do tego moduł agregacji świec wycinał soboty i niedziele,
co dla forex jest poprawne, a dla rynku 24/7 usuwa ok. 29% danych. Rollover krypto naliczany jest 7 dni w tygodniu, nie 5.
## Zasada ogólna
Backtester ma ukryte założenia o rynku (godziny handlu, koszty, punkt, swap). Przeniesienie strategii na
inną klasę aktywów bez zmiany tych założeń daje liczby, które wyglądają wiarygodnie i są błędne.
## Jak wykryć u siebie
Policz świece na tydzień w danych wejściowych do backtestu i porównaj z oczekiwanymi dla rynku
(24/7 vs 24/5). Wypisz koszt jednej transakcji w walucie konta i porównaj ze specyfikacją u brokera.
Każda rozbieżność = złe założenie o instrumencie.
## Liczby
- Brakujące świece BTC przed poprawką: ok. 29%.
- Udział świec w środku weekendu w realnych danych: BTC 25%, EURUSD M1 0% (próg rozpoznania rynku 24/7: 5%).
- Testy silnika po poprawce: 146 (28 nowych).
## Można pokazać
- Wykres liczby świec na dzień tygodnia: BTC vs EURUSD.
- Tabela profili kosztów forex vs krypto (struktura, bez wartości kalibracji brokera).
## Nie pokazywać
- Nazwy brokera, konfiguracji serwerów i adresów.
