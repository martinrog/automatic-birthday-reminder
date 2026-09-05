# 🎂 Verjaardag Reminder

Serverless verjaardagsherinnering: draait volledig op **GitHub Actions**
(gratis, geen eigen server nodig) en stuurt een **pushnotificatie** naar je
telefoon via [ntfy.sh](https://ntfy.sh) als iemand uit je lijst jarig is.

## Hoe het werkt

Het systeem houdt niets bij en draait niet continu — het begint elke keer
met een schone lei en doet in een paar seconden zijn werk:

1. **GitHub Actions start de workflow op een vast schema (cron).** Elke dag
   op twee momenten: `06:00` en `07:00` UTC. Dat is een timer aan GitHub's
   kant; er hoeft niets "aan te staan".
2. **Twee tijden vanwege zomer-/wintertijd.** In de zomer (CEST, UTC+2) is
   `06:00 UTC` = 08:00 bij jou; in de winter (CET, UTC+1) is `07:00 UTC` =
   08:00. Beide runs starten altijd, maar het script checkt zelf of het
   *nu* echt 08:00 lokale tijd (Europe/Amsterdam) is en stopt anders meteen.
   Zo hoef je de cron nooit aan te passen.
3. **De lijst wordt élke run vers opgehaald.** De workflow downloadt telkens
   de huidige `birthdays.json` uit de privé-repo (zie hieronder). Er is geen
   cache en geen wijzigingsdetectie: wat er op dat moment staat, wordt
   gebruikt. Pas je de lijst aan, dan pikt de eerstvolgende ochtend-run dat
   automatisch op — je hoeft niets te triggeren.
4. **Vergelijken met vandaag.** Alleen om 08:00 loopt het script door de
   lijst en vergelijkt per persoon `(dag, maand)` met de datum van vandaag.
   Voor elke match gaat er een pushnotificatie naar je telefoon.

```
Elke dag, 2×:  GitHub cron start de workflow
      │
      ├─ haalt verse birthdays.json uit de privé-repo op
      ├─ is het nu 08:00 in NL?  nee → stop  |  ja ↓
      ├─ loop door alle namen: is (dag, maand) == vandaag?
      └─ voor elke match → stuur ntfy-melding 📲
```

## Setup

1. **Installeer de ntfy-app** op je telefoon ([iOS](https://apps.apple.com/app/ntfy/id1625396347) / [Android](https://play.google.com/store/apps/details?id=io.heckel.ntfy)).
2. **Verzin een geheim topic**, bijvoorbeeld `martin-verjaardagen-x7f2q9`
   (hoe onvoorspelbaarder, hoe beter — iedereen die de topicnaam kent kan
   meelezen).
3. **Abonneer** je in de app op dat topic.
4. **Zet het topic als GitHub Secret**: ga naar
   `Settings → Secrets and variables → Actions → New repository secret`,
   naam `NTFY_TOPIC`, waarde je gekozen topic.
5. **De verjaardagslijst** staat in een **aparte privé-repo** (`birthday-list`)
   in het bestand `birthdays.json`. Zo blijft persoonlijke data uit deze
   publieke repo. De workflow haalt dat bestand op via een read-only
   deploy key (opgeslagen als secret `DATA_DEPLOY_KEY`).
   Bijwerken kan makkelijk vanaf je telefoon met de **GitHub-app**: open de
   privé-repo → `birthdays.json` → potloodje → aanpassen → commit.
   Formaat: `date` is `DD-MM` (Nederlands, bv. `19-04` = 19 april), `year`
   is optioneel — vul je die in, dan komt de leeftijd in het bericht. Zie
   [`birthdays.example.json`](birthdays.example.json) als sjabloon. Lege
   sjabloon-regels (`"date": "DD-MM"`) triggeren nooit een melding, dus die
   mag je laten staan om snel een nieuwe regel te kunnen invullen.
6. Klaar. Test het meteen via het tabblad **Actions → Check birthdays →
   Run workflow** (handmatige trigger), zodat je niet hoeft te wachten
   tot 8:00 uur.

> **Lokaal testen?** Zet een `birthdays.json` in deze map (staat in
> `.gitignore`) — het script leest dat bestand. Je kunt ook de
> `BIRTHDAYS_JSON` omgevingsvariabele zetten; die krijgt voorrang.

## Bestanden

| Bestand | Doel |
|---|---|
| `birthdays.example.json` | Sjabloon voor de verjaardagslijst (formaat) |
| `check_birthdays.py` | Checkt of iemand jarig is en stuurt de notificatie |
| `tests/` | Unit tests (`python -m unittest discover -s tests`) |
| `.github/workflows/check_birthdays.yml` | De dagelijkse trigger |
| `.github/workflows/tests.yml` | Draait de unit tests bij elke push |
| `requirements.txt` | Python dependencies |

> `birthdays.json` staat bewust **niet** in deze repo (privacy) — de echte
> lijst leeft in de aparte privé-repo `birthday-list`.
