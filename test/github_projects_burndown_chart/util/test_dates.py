import os
import sys
import unittest
from datetime import timezone

sys.path.insert(0, os.path.abspath(os.path.join(
    os.path.dirname(__file__), '..', '..', '..', 'src', 'github_projects_burndown_chart')))

from util.dates import parse_to_utc


class TestDates(unittest.TestCase):

    def test_parse_to_utc_respects_explicit_timezone_offset(self):
        dt = parse_to_utc('2026-02-08T18:37:00-05:00')

        self.assertEqual(2026, dt.year)
        self.assertEqual(2, dt.month)
        self.assertEqual(8, dt.day)
        self.assertEqual(23, dt.hour)
        self.assertEqual(37, dt.minute)
        self.assertEqual(timezone.utc, dt.tzinfo)

    def test_parse_to_utc_naive_date_returns_utc_datetime(self):
        dt = parse_to_utc('2026-02-08')

        self.assertEqual(timezone.utc, dt.tzinfo)


if __name__ == '__main__':
    unittest.main()
