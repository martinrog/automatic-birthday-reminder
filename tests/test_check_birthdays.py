"""Unit tests voor check_birthdays.

Draai vanuit de projectmap:  python -m unittest discover -s tests
"""

import os
import sys
import unittest
from datetime import datetime
from unittest import mock
from zoneinfo import ZoneInfo

# Zorg dat check_birthdays importeerbaar is, ongeacht van waar je test draait.
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import check_birthdays as cb  # noqa: E402

TZ = ZoneInfo("Europe/Amsterdam")


class TestParseDate(unittest.TestCase):
    def test_valid_dd_mm(self):
        self.assertEqual(cb.parse_date("19-04"), (19, 4))
        self.assertEqual(cb.parse_date("05-11"), (5, 11))
        self.assertEqual(cb.parse_date("1-1"), (1, 1))

    def test_template_placeholder_is_invalid(self):
        self.assertIsNone(cb.parse_date("DD-MM"))

    def test_empty_and_malformed(self):
        self.assertIsNone(cb.parse_date(""))
        self.assertIsNone(cb.parse_date("3"))
        self.assertIsNone(cb.parse_date("1-2-3"))
        self.assertIsNone(cb.parse_date(None))

    def test_out_of_range(self):
        self.assertIsNone(cb.parse_date("13-13"))  # maand 13
        self.assertIsNone(cb.parse_date("40-01"))  # dag 40
        self.assertIsNone(cb.parse_date("00-05"))  # dag 0

    def test_us_format_mistake_is_rejected(self):
        # Iemand die per ongeluk MM-DD typt voor 19 april: "04-19"
        # -> dag 4, maand 19 -> ongeldig, niet stilletjes 19 april.
        self.assertIsNone(cb.parse_date("04-19"))


class TestBirthdaysToday(unittest.TestCase):
    def setUp(self):
        self.people = [
            {"name": "Sanne", "date": "14-03"},
            {"name": "Tim", "date": "22-07", "year": 1999},
            {"name": "Eefje", "date": "19-04"},
        ]

    def test_matches_on_correct_day(self):
        now = datetime(2026, 4, 19, 8, 0, tzinfo=TZ)
        matches = cb.birthdays_today(self.people, now)
        self.assertEqual([p["name"] for p in matches], ["Eefje"])

    def test_dutch_format_not_misread_as_month(self):
        # "19-04" moet 19 april zijn, NIET 4 april.
        self.assertEqual(cb.birthdays_today(self.people, datetime(2026, 4, 4, 8, 0, tzinfo=TZ)), [])
        self.assertEqual(
            [p["name"] for p in cb.birthdays_today(self.people, datetime(2026, 4, 19, 8, 0, tzinfo=TZ))],
            ["Eefje"],
        )

    def test_no_match(self):
        self.assertEqual(cb.birthdays_today(self.people, datetime(2026, 1, 1, 8, 0, tzinfo=TZ)), [])

    def test_multiple_matches_same_day(self):
        people = [
            {"name": "A", "date": "01-06"},
            {"name": "B", "date": "01-06"},
        ]
        now = datetime(2026, 6, 1, 8, 0, tzinfo=TZ)
        self.assertEqual([p["name"] for p in cb.birthdays_today(people, now)], ["A", "B"])

    def test_empty_template_rows_are_skipped_silently(self):
        people = [
            {"name": "", "date": "DD-MM"},
            {"name": "  ", "date": "01-01"},
        ]
        now = datetime(2026, 1, 1, 8, 0, tzinfo=TZ)
        with mock.patch("sys.stderr"):
            self.assertEqual(cb.birthdays_today(people, now), [])

    def test_named_row_with_invalid_date_warns(self):
        people = [{"name": "Foutje", "date": "40-13"}]
        now = datetime(2026, 1, 1, 8, 0, tzinfo=TZ)
        with mock.patch("sys.stderr") as err:
            result = cb.birthdays_today(people, now)
        self.assertEqual(result, [])
        # Er is een waarschuwing naar stderr geschreven.
        self.assertTrue(err.write.called)


class TestBuildMessage(unittest.TestCase):
    def test_with_age(self):
        msg = cb.build_message("Tim", 27)
        self.assertIn("Tim", msg)
        self.assertIn("27 jaar", msg)
        self.assertTrue(msg.startswith("🎂"))

    def test_without_age(self):
        msg = cb.build_message("Sanne", None)
        self.assertIn("Sanne", msg)
        self.assertIn("jarig", msg)


class TestSendNotificationHeaders(unittest.TestCase):
    def test_headers_are_latin1_safe(self):
        # Regressietest: emoji hoort in de body, niet in de headers.
        captured = {}

        class FakeResp:
            def raise_for_status(self):
                pass

        def fake_post(url, data=None, headers=None, timeout=None):
            captured.update(url=url, data=data, headers=headers)
            return FakeResp()

        with mock.patch.object(cb.requests, "post", fake_post):
            cb.send_notification("topic", "Tim", 27)

        for key, value in captured["headers"].items():
            value.encode("latin-1")  # faalt als er een niet-latin-1 teken in zit
        # Body is UTF-8 en bevat de emoji.
        self.assertIn("🎂", captured["data"].decode("utf-8"))
        self.assertTrue(captured["url"].endswith("/topic"))


if __name__ == "__main__":
    unittest.main()
