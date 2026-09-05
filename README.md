# 🎂 Verjaardag Reminder

Serverless verjaardagsherinnering: draait volledig op **GitHub Actions**
(gratis, geen eigen server nodig) en stuurt een **pushnotificatie** naar je
telefoon via [ntfy.sh](https://ntfy.sh) als iemand uit je lijst jarig is.

## Hoe het werkt

- Een GitHub Actions workflow draait elke dag automatisch.
- Het script (`check_birthdays.py`) checkt of het écht 8:00 lokale tijd
  (Europe/Amsterdam) is — de workflow triggert op twee UTC-tijden om de
  zomer-/wintertijdwissel automatisch op te vangen, zonder dat je ooit de
  cron hoeft aan te passen.
- Als iemand uit `birthdays.json` vandaag jarig is, gaat er een
  pushnotificatie naar je telefoon.

## Setup

1. **Installeer de ntfy-app** op je telefoon ([iOS](https://apps.apple.com/app/ntfy/id1625396347) / [Android](https://play.google.com/store/apps/details?id=io.heckel.ntfy)).
2. **Verzin een geheim topic**, bijvoorbeeld `martin-verjaardagen-x7f2q9`
   (hoe onvoorspelbaarder, hoe beter — iedereen die de topicnaam kent kan
   meelezen).
3. **Abonneer** je in de app op dat topic.
4. **Zet het topic als GitHub Secret**: ga naar
   `Settings → Secrets and variables → Actions → New repository secret`,
   naam `NTFY_TOPIC`, waarde je gekozen topic.
5. **Vul `birthdays.json`** aan met je eigen lijst (formaat: `MM-DD`,
   `year` is optioneel — als je die invult wordt de leeftijd in het
   bericht vermeld).
6. Klaar. Test het meteen via het tabblad **Actions → Check birthdays →
   Run workflow** (handmatige trigger), zodat je niet hoeft te wachten
   tot 8:00 uur.

## Bestanden

| Bestand | Doel |
|---|---|
| `birthdays.json` | Lijst met namen + geboortedatums |
| `check_birthdays.py` | Checkt of iemand jarig is en stuurt de notificatie |
| `.github/workflows/check_birthdays.yml` | De dagelijkse trigger |
| `requirements.txt` | Python dependencies |
