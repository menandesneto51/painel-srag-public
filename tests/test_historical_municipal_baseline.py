# -*- coding: utf-8 -*-
import json
import tempfile
import unittest
from pathlib import Path

import pandas as pd

from src.historical_baseline import (
    build_municipal_weekly,
    municipality_valid_from_year,
    robust_municipal_weekly_baseline,
)


class MunicipalHistoricalBaselineTests(unittest.TestCase):
    def make_reference(self, path: Path):
        rows = [
            {"codigo_ibge": "5101837", "municipio": "Boa Esperança do Norte", "populacao": 6000},
            {"codigo_ibge": "5103403", "municipio": "Cuiabá", "populacao": 700000},
        ]
        used = {"510183", "510340"}
        candidate = 1
        while len(rows) < 142:
            prefix = f"510{candidate:03d}"
            candidate += 1
            if prefix in used:
                continue
            used.add(prefix)
            rows.append({
                "codigo_ibge": prefix + "0",
                "municipio": f"Município Teste {len(rows)}",
                "populacao": 1000,
            })
        pd.DataFrame(rows).to_csv(path, index=False)

    def make_harmonization(self, path: Path):
        path.write_text(
            json.dumps({
                "default_valid_from_year": 2019,
                "exceptions": {
                    "5101837": {
                        "municipio": "Boa Esperança do Norte",
                        "valid_from_year": 2025,
                    }
                },
            }),
            encoding="utf-8",
        )

    def make_sivep(self, path: Path, year: int):
        rows = [
            {"SG_UF": "MT", "CO_MUN_RES": "510340", "SEM_PRI": f"{year}01"},
            {"SG_UF": "MT", "CO_MUN_RES": "510340", "SEM_PRI": f"{year}02"},
            {"SG_UF": "MT", "CO_MUN_RES": "510183", "SEM_PRI": f"{year}02"},
        ]
        pd.DataFrame(rows).to_csv(path, sep=";", index=False)

    def test_boa_esperanca_valid_only_from_2025(self):
        harmonization = {
            "default_valid_from_year": 2019,
            "exceptions": {"5101837": {"valid_from_year": 2025}},
        }
        self.assertEqual(
            municipality_valid_from_year("5101837", harmonization),
            2025,
        )
        self.assertEqual(
            municipality_valid_from_year("5103403", harmonization),
            2019,
        )

    def test_zero_fill_respects_territorial_validity(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            ref = root / "population.csv"
            harmon = root / "harmon.json"
            sivep2019 = root / "sivep2019.csv"
            sivep2025 = root / "sivep2025.csv"
            self.make_reference(ref)
            self.make_harmonization(harmon)
            self.make_sivep(sivep2019, 2019)
            self.make_sivep(sivep2025, 2025)

            m2019, meta2019 = build_municipal_weekly(
                sivep2019, 2019, ref, harmon
            )
            m2025, meta2025 = build_municipal_weekly(
                sivep2025, 2025, ref, harmon
            )

            self.assertEqual(meta2019["municipalities_valid_in_year"], 141)
            self.assertEqual(meta2025["municipalities_valid_in_year"], 142)
            self.assertFalse((m2019["codigo_ibge"].astype(str) == "5101837").any())
            self.assertTrue((m2025["codigo_ibge"].astype(str) == "5101837").any())

    def test_municipal_baseline_keeps_available_year_count(self):
        df = pd.DataFrame({
            "ano": [2023, 2024, 2025, 2025],
            "SE": [1, 1, 1, 1],
            "codigo_ibge": ["5103403", "5103403", "5103403", "5101837"],
            "municipio": ["Cuiabá", "Cuiabá", "Cuiabá", "Boa Esperança do Norte"],
            "zero_fill_authorized": [True, True, True, True],
            "casos": [10, 12, 14, 3],
        })
        baseline = robust_municipal_weekly_baseline(
            df, "casos", [2023, 2024, 2025]
        )
        cuiaba = baseline.loc[baseline["codigo_ibge"] == "5103403"].iloc[0]
        boa = baseline.loc[baseline["codigo_ibge"] == "5101837"].iloc[0]
        self.assertEqual(int(cuiaba["n_years"]), 3)
        self.assertEqual(int(boa["n_years"]), 1)


if __name__ == "__main__":
    unittest.main()
