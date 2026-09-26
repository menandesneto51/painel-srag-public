# -*- coding: utf-8 -*-
import json
import tempfile
import unittest
from pathlib import Path

import pandas as pd

from scripts.build_public_snapshot_v2 import build_snapshot


class PublicSnapshotBuilderTests(unittest.TestCase):
    def test_builder_uses_stable_week_for_recent_incidence(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            candidate = root / "candidate"
            output = candidate / "public_snapshot"
            candidate.mkdir(parents=True)

            pd.DataFrame([
                {"SE": 9, "casos": 10, "hospitalizacoes": 8, "uti": 2, "obitos": 1, "curas": 7},
                {"SE": 10, "casos": 12, "hospitalizacoes": 10, "uti": 2, "obitos": 1, "curas": 9},
                {"SE": 11, "casos": 20, "hospitalizacoes": 15, "uti": 3, "obitos": 2, "curas": 12},
                {"SE": 12, "casos": 30, "hospitalizacoes": 20, "uti": 4, "obitos": 3, "curas": 15},
            ]).to_csv(candidate / "weekly_srag_mt_2026.csv", index=False)

            municipalities = []
            weekly_mun = []
            for i in range(142):
                code = f"510{i:03d}0"
                pop = 1000
                cases = 0
                if i == 0:
                    code = "5103403"
                    cases = 7
                    weekly_mun.extend([
                        {"codigo_ibge": code, "municipio": "Cuiabá", "populacao": pop, "SE": 9, "casos": 1,
                         "hospitalizacoes": 1, "uti": 0, "obitos": 0, "curas": 1},
                        {"codigo_ibge": code, "municipio": "Cuiabá", "populacao": pop, "SE": 10, "casos": 2,
                         "hospitalizacoes": 2, "uti": 0, "obitos": 0, "curas": 2},
                        {"codigo_ibge": code, "municipio": "Cuiabá", "populacao": pop, "SE": 11, "casos": 4,
                         "hospitalizacoes": 3, "uti": 1, "obitos": 1, "curas": 2},
                    ])
                    name = "Cuiabá"
                else:
                    name = f"Município {i}"
                municipalities.append({
                    "codigo_ibge": code,
                    "codigo_sivep_6": code[:6],
                    "municipio": name,
                    "populacao": pop,
                    "casos": cases,
                    "hospitalizacoes": cases,
                    "uti": 1 if i == 0 else 0,
                    "obitos": 1 if i == 0 else 0,
                    "curas": 5 if i == 0 else 0,
                })

            pop_total = sum(x["populacao"] for x in municipalities)
            # Ajustar o primeiro município para reproduzir o total oficial usado pelos gates.
            municipalities[0]["populacao"] += 3_950_330 - pop_total
            for row in weekly_mun:
                if row["codigo_ibge"] == "5103403":
                    row["populacao"] = municipalities[0]["populacao"]

            pd.DataFrame(municipalities).to_csv(
                candidate / "municipal_srag_mt_2026.csv", index=False
            )
            pd.DataFrame(weekly_mun).to_csv(
                candidate / "municipal_weekly_srag_mt_2026.csv", index=False
            )
            (candidate / "sivep_mt_2026_metadata.json").write_text(
                json.dumps({
                    "reference_year": 2026,
                    "max_observed_week": 12,
                    "stable_week_provisional": 10,
                }),
                encoding="utf-8",
            )
            (candidate / "stability_delay_estimate.json").write_text(
                json.dumps({
                    "status": "provisional_until_vintage_backtest",
                    "provisional_case_stable_week": 10,
                    "provisional_outcome_stable_week": 9,
                }),
                encoding="utf-8",
            )

            sources = root / "sources.json"
            sources.write_text(
                json.dumps({
                    "sources": {
                        "sivep_gripe_2026": {
                            "resource_date": "2026-09-14",
                            "resource_id": "test",
                            "url": "https://example.test/sivep.csv",
                        }
                    }
                }),
                encoding="utf-8",
            )

            metadata = build_snapshot(candidate, output, sources, recent_window_weeks=2)
            risk = pd.read_csv(output / "risk_summary_v2_candidate.csv")
            cuiaba = risk.loc[risk["codigo_ibge"].astype(str) == "5103403"].iloc[0]

            self.assertEqual(metadata["stable_week_cases"], 10)
            self.assertEqual(metadata["stable_week_outcomes"], 9)
            self.assertEqual(metadata["publication_status"], "under_review")
            self.assertEqual(int(cuiaba["casos_recentes"]), 3)
            self.assertEqual(int(cuiaba["recent_window_start_se"]), 9)
            self.assertEqual(int(cuiaba["recent_window_end_se"]), 10)
            self.assertEqual(cuiaba["score_v2_status"], "under_calibration")

            forecast = pd.read_csv(output / "forecast_summary.csv")
            self.assertTrue(forecast.empty)


if __name__ == "__main__":
    unittest.main()
