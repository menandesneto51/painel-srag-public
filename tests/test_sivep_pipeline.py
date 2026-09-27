# -*- coding: utf-8 -*-
import unittest

from src.sivep_pipeline import ibge7_to_sivep6, normalize_week


class SivepPipelineTests(unittest.TestCase):
    def test_normalize_year_week(self):
        self.assertEqual(normalize_week("202601", 2026), 1)
        self.assertEqual(normalize_week("202653", 2026), 53)

    def test_reject_other_year(self):
        self.assertIsNone(normalize_week("202552", 2026))

    def test_reject_invalid_week(self):
        self.assertIsNone(normalize_week("202600", 2026))
        self.assertIsNone(normalize_week("202654", 2026))

    def test_accept_week_only(self):
        self.assertEqual(normalize_week("16", 2026), 16)

    def test_ibge_to_sivep_mapping(self):
        self.assertEqual(ibge7_to_sivep6("5103403"), "510340")
        self.assertEqual(ibge7_to_sivep6("5108402"), "510840")

    def test_ibge_mapping_rejects_invalid_code(self):
        with self.assertRaises(ValueError):
            ibge7_to_sivep6("3550308")


if __name__ == "__main__":
    unittest.main()
