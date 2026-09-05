"""
Checkt of iemand uit birthdays.json vandaag jarig is en stuurt zo ja
een pushnotificatie via ntfy.sh.

Dit script wordt getriggerd door de GitHub Actions workflow, twee keer
per dag (om de zomer-/wintertijd-wissel op te vangen). Het script zelf
bepaalt of het NU echt 8:00 lokale tijd (Europe/Amsterdam) is, en stuurt
alleen dan een melding. Zo hoeft niemand de cron twee keer per jaar aan
te passen.

Datumformaat: DD-MM (Nederlands), bv. "19-04" = 19 april. Het jaar is
optioneel; vul je die in, dan komt de leeftijd in het bericht.
"""

import json
import os
import sys
from datetime import datetime
from zoneinfo import ZoneInfo

import requests

TARGET_HOUR = 8  # lokale tijd waarop je de melding wil ontvangen
DATA_FILE = os.path.join(os.path.dirname(__file__), "birthdays.json")
NOTIFICATION_TITLE = "Verjaardag!"  # ASCII: HTTP-headers moeten latin-1 zijn


def load_birthdays():
    """Laadt de verjaardagslijst.

    Voorkeur: de BIRTHDAYS_JSON secret (zodat persoonlijke data niet in de
    publieke repo hoeft te staan). Valt terug op een lokale birthdays.json,
    handig voor lokaal testen.
    """
    raw = os.environ.get("BIRTHDAYS_JSON")
    if raw:
        return json.loads(raw)

    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            return json.load(f)

    print(
        "Geen BIRTHDAYS_JSON secret en geen lokale birthdays.json gevonden.",
        file=sys.stderr,
    )
    sys.exit(1)


def parse_date(date_str):
    """Parseert een 'DD-MM'-datum naar (dag, maand).

    Geeft None terug bij een ongeldige/onparseerbare datum (bv. een lege
    sjabloon-regel of een per ongeluk als MM-DD ingevulde datum).
    """
    try:
        day, month = (int(part) for part in date_str.split("-"))
    except (ValueError, AttributeError):
        return None
    if not (1 <= month <= 12 and 1 <= day <= 31):
        return None
    return day, month


def birthdays_today(birthdays, now):
    """Geeft de personen terug die op de datum van `now` jarig zijn.

    Lege sjabloon-regels (zonder naam) worden stil overgeslagen; regels met
    een naam maar een ongeldige datum leveren een waarschuwing op, zodat een
    typefout niet ongemerkt blijft.
    """
    matches = []
    for person in birthdays:
        name = (person.get("name") or "").strip()
        if not name:
            continue  # lege sjabloon-regel

        parsed = parse_date(person.get("date", ""))
        if parsed is None:
            print(
                f"Waarschuwing: ongeldige datum voor '{name}': "
                f"{person.get('date')!r} (verwacht DD-MM). Overgeslagen.",
                file=sys.stderr,
            )
            continue

        if (now.day, now.month) == parsed:
            matches.append(person)
    return matches


def build_message(name, age):
    """Bouwt de berichttekst (emoji in de body, die gaat als UTF-8)."""
    if age is not None:
        return f"🎂 {name} wordt vandaag {age} jaar. Vergeet niet te feliciteren!"
    return f"🎂 {name} is vandaag jarig. Vergeet niet te feliciteren!"


def send_notification(topic: str, name: str, age: int | None):
    resp = requests.post(
        f"https://ntfy.sh/{topic}",
        data=build_message(name, age).encode("utf-8"),
        headers={
            "Title": NOTIFICATION_TITLE,
            "Tags": "birthday,tada",
            "Priority": "default",
        },
        timeout=10,
    )
    resp.raise_for_status()
    print(f"Notificatie verstuurd voor {name}.")


def main():
    now = datetime.now(ZoneInfo("Europe/Amsterdam"))

    if now.hour != TARGET_HOUR:
        print(f"Nu is het {now.hour}:xx lokale tijd, niet {TARGET_HOUR}:xx. Skip.")
        return

    topic = os.environ.get("NTFY_TOPIC")
    if not topic:
        print("Geen NTFY_TOPIC secret gevonden, kan niks versturen.", file=sys.stderr)
        sys.exit(1)

    birthdays = load_birthdays()
    matches = birthdays_today(birthdays, now)

    if not matches:
        print(f"Niemand is vandaag ({now:%d-%m}) jarig.")
        return

    for person in matches:
        age = now.year - person["year"] if "year" in person else None
        send_notification(topic, person["name"], age)


if __name__ == "__main__":
    main()
