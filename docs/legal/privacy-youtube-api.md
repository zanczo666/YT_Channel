# Szkic: polityka prywatności dla audytu YouTube API (D4)

Do wklejenia na stronę jako osobna podstrona, np. `/privacy-youtube`, gdy właściciel zdecyduje o stronie
(`CLAUDE.md`: na razie nie linkujemy quantinvest.co z kanału, ale audyt wymaga publicznego adresu polityki).
Przed publikacją sprawdź treść z prawnikiem — to szkic techniczny, nie porada prawna. `<EMAIL>` uzupełnia właściciel.

---

## Privacy Policy — YouTube API Services

Last updated: <DATE>

This policy describes how the publishing tools of the YouTube channel "Radoslaw Lubas - Systematic Trading Lab"
("the Application") use YouTube API Services.

**Who uses the Application.** The Application is used only by the channel owner to manage his own YouTube channel.
It is not offered to other users.

**Data accessed.** With the owner's authorization, the Application accesses: the owner's channel and video
metadata, uploads (videos, thumbnails, captions), playlists, public comments on the owner's videos, and
YouTube Analytics reports for the owner's videos.

**How the data is used.** To upload and schedule the owner's videos, add captions and playlists, prepare
draft replies to comments for the owner's review, and produce performance reports for the owner.
Comment authors' public display names and comment texts are stored only in the owner's private working files
for review and are not shared, sold, or used for advertising.

**Storage and security.** OAuth tokens are stored on the owner's private server with file permissions
restricted to the owner and are never published. Data is kept only as long as needed for the purposes above.

**Revoking access.** Access can be revoked at any time at https://myaccount.google.com/permissions.

**Google policies.** The Application uses YouTube API Services; by using it you agree to the YouTube Terms of
Service (https://www.youtube.com/t/terms). Google Privacy Policy: https://policies.google.com/privacy.

**Contact.** <EMAIL>

---

## Wniosek o audyt — co przygotować
1. Opublikowana polityka pod stałym adresem (powyżej).
2. Projekt Google Cloud `yt-channel-research-513011`, ekran zgody OAuth z nazwą aplikacji, adresem polityki i domeną.
3. Formularz „YouTube API Services – Audit and Quota Extension”: opis użycia (zarządzanie własnym kanałem,
   wgrywanie i planowanie publikacji), zakresy z `scripts/yt_api.py`, zrzuty ekranu przepływu.
4. Do czasu zatwierdzenia filmy wgrane przez API są prywatne; publikację ustawiasz w Studio.
