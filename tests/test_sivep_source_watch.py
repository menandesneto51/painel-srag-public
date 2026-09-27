# -*- coding: utf-8 -*-
import unittest

from scripts.check_sivep_source import latest_2026_csv, parse_date_from_url


class SivepSourceWatchTests(unittest.TestCase):
    def test_parse_date_from_url(self):
        url = "https://s3.sa-east-1.amazonaws.com/ckan.saude.gov.br/SRAG/2026/INFLUD26-14-09-2026.csv"
        self.assertEqual(parse_date_from_url(url).isoformat(), "2026-09-14")

    def test_ignore_other_year(self):
        url = "https://s3.sa-east-1.amazonaws.com/ckan.saude.gov.br/SRAG/2025/INFLUD25-14-09-2026.csv"
        self.assertIsNone(parse_date_from_url(url))

    def test_latest_resource(self):
        resources = [
            {
                "name": "2026- Banco vivo 14/09/2026 - CSV",
                "format": "CSV",
                "url": "https://x/SRAG/2026/INFLUD26-14-09-2026.csv",
                "id": "a",
            },
            {
                "name": "2026- Banco vivo 21/09/2026 - CSV",
                "format": "CSV",
                "url": "https://x/SRAG/2026/INFLUD26-21-09-2026.csv",
                "id": "b",
            },
            {
                "name": "2026 JSON",
                "format": "JSON",
                "url": "https://x/SRAG/2026/INFLUD26-28-09-2026.json",
                "id": "c",
            },
        ]
        latest = latest_2026_csv(resources)
        self.assertEqual(latest["resource_date"], "2026-09-21")
        self.assertEqual(latest["id"], "b")


if __name__ == "__main__":
    unittest.main()
