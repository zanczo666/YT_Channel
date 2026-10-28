# Face lock — zasady zdjęć twarzy

Cel: ta sama, rozpoznawalna twarz w każdej miniaturze (wniosek z analizy 2026-10-28).

| Plik | Nastrój | Użycie |
|---|---|---|
| `face-neutral.png` | spokojny, wzrok w kamerę | Validation Gates, intro |
| `face-skeptic.png` | lekko sceptyczny, uniesiona brew | FAIL, Strategy Graveyard, Paper vs Reality |
| `face-explain.png` | tłumaczy, gest dłonią | Validation Gates, The Funnel |
| `face-pass.png` (opcjonalnie) | lekki uśmiech, pewność | PASS |

Zasady: to samo światło (z przodu, z okna), ten sam strój lub podobny, kadr od klatki piersiowej, tło wycięte
(PNG z przezroczystością), min. 1000 px wysokości. Bez przesadnej mimiki (standard §3).
Jeśli kiedyś włączymy generowanie AI — te same pliki są referencją twarzy.

## Stan (2026-10-28)
Surowe zdjęcia: `raw/` (7 szt.), wycięte tło: `cut/` (rembg, lokalnie: `scripts/face_cutout.py`). Przypisanie:
- `face-neutral.png` ← IMG_20261028_222839
- `face-skeptic.png` ← IMG_20261028_222852 (uniesiona brew)
- `face-squint.png` ← IMG_20261028_222930 (zmrużone oczy, sceptycyzm)
- `face-pass.png` ← IMG_20261028_222940 (lekki uśmiech)

Do poprawy przy następnej sesji zdjęć: telefon na wysokości oczu (nie z dołu), 1–1,5 m, zoom 2×, samowyzwalacz
(bez ręki w kadrze), gładka koszulka bez dużego nadruku.
