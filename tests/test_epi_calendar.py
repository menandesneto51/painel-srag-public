# -*- coding: utf-8 -*-
import unittest

from src.epi_calendar import (
    epidemiological_week1_start,
    epidemiological_week_end,
    epidemiological_week_start,
    epidemiological_weeks_in_year,
)


class EpidemiologicalCalendarTests(unittest.TestCase):
    def test_official_2026_reference_dates(self):
        self.assertEqual(epidemiological_week1_start(2026).isoformat(), "2026-01-04")
        self.assertEqual(epidemiological_week_start(2026, 10).isoformat(), "2026-03-08")
        self.assertEqual(epidemiological_week_start(2026, 38).isoformat(), "2026-09-20")
        self.assertEqual(epidemiological_week_end(2026, 52).isoformat(), "2027-01-02")

    def test_2026_has_52_weeks(self):
        self.assertEqual(epidemiological_weeks_in_year(2026), 52)
        with self.assertRaises(ValueError):
            epidemiological_week_start(2026, 53)

    def test_week_count_is_52_or_53(self):
        for year in range(2019, 2027):
            self.assertIn(epidemiological_weeks_in_year(year), {52, 53})


if __name__ == "__main__":
    unittest.main()
