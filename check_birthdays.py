"""
Checkt of iemand uit birthdays.json vandaag jarig is en stuurt zo ja
een pushnotificatie via ntfy.sh.

Dit script wordt getriggerd door de GitHub Actions workflow, twee keer
per dag (om de zomer-/wintertijd-wissel op te vangen). Het script zelf
bepaalt of het NU echt 8:00 lokale tijd (Europe/Amsterdam) is, en stuurt
alleen dan een melding. Zo hoeft niemand de cron twee keer per jaar aan
te passen.
"""

import json
import os
import sys
from datetime import datetime
from zoneinfo import ZoneInfo

import requests

TARGET_HOUR = 8  # lokale tijd waarop je de melding wil ontvangen
DATA_FILE = os.path.join(os.path.dirname(__file__), "birthdays.json")


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


def send_notification(topic: str, name: str, age: int | None):
    # Let op: HTTP-headers moeten latin-1 zijn, dus geen emoji in Title.
    # De emoji zetten we in de body (die versturen we als UTF-8).
    title = "Verjaardag!"
    if age is not None:
        message = f"🎂 {name} wordt vandaag {age} jaar. Vergeet niet te feliciteren!"
    else:
        message = f"🎂 {name} is vandaag jarig. Vergeet niet te feliciteren!"

    resp = requests.post(
        f"https://ntfy.sh/{topic}",
        data=message.encode("utf-8"),
        headers={
            "Title": title,
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

    today = now.strftime("%m-%d")
    birthdays = load_birthdays()

    matches = [b for b in birthdays if b.get("date") == today]

    if not matches:
        print(f"Niemand is vandaag ({today}) jarig.")
        return

    for person in matches:
        age = None
        if "year" in person:
            age = now.year - person["year"]
        send_notification(topic, person["name"], age)


if __name__ == "__main__":
    main()
