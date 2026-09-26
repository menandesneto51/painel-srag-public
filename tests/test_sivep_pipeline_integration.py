# -*- coding: utf-8 -*-
import json
import tempfile
import unittest
from pathlib import Path

import pandas as pd

from src.sivep_pipeline import build_mt_aggregates


class SivepPipelineIntegrationTests(unittest.TestCase):
    def make_population(self, path: Path):
        rows = [
            {"codigo_ibge": "5103403", "municipio": "Cuiabá", "populacao": 700000},
            {"codigo_ibge": "5108402", "municipio": "Várzea Grande", "populacao": 320000},
        ]
        used_prefixes = {"510340", "510840"}
        candidate = 10000
        while len(rows) < 142:
            prefix = f"51{candidate:04d}"
            candidate += 1
            if prefix in used_prefixes:
                continue
            used_prefixes.add(prefix)
            rows.append({
                "codigo_ibge": prefix + "0",
                "municipio": f"Município Teste {len(rows)}",
                "populacao": 1000,
            })
        pd.DataFrame(rows).to_csv(path, index=False)

    def make_config(self, path: Path):
        config = {
            "reference_year": 2026,
            "territorial_scope": {
                "residence_uf_field": "SG_UF",
                "residence_uf_value": "MT",
                "municipality_code_candidates": ["CO_MUN_RES"],
                "municipality_name_candidates": ["ID_MN_RESI"],
            },
            "time": {
                "symptom_week_field": "SEM_PRI",
                "symptom_date_field": "DT_SIN_PRI",
                "stable_week_policy": {
                    "mode": "lag_from_latest_observed",
                    "lag_weeks": 2,
                    "status": "provisional",
                    "requires_backtesting": True,
                },
            },
            "severity": {
                "hospital_field": "HOSPITAL",
                "hospital_yes": ["1"],
                "icu_field": "UTI",
                "icu_yes": ["1"],
                "outcome_field": "EVOLUCAO",
                "cure": ["1"],
                "death": ["2"],
                "death_other_causes": ["3"],
                "ignored": ["9"],
            },
        }
        path.write_text(json.dumps(config), encoding="utf-8")

    def make_sivep(self, path: Path):
        rows = [
            {
                "SG_UF": "MT",
                "CO_MUN_RES": "510340",
                "SEM_PRI": "202610",
                "DT_SIN_PRI": "02/03/2026",
                "HOSPITAL": "1",
                "UTI": "1",
                "EVOLUCAO": "2",
            },
            {
                "SG_UF": "MT",
                "CO_MUN_RES": "510340",
                "SEM_PRI": "202611",
                "DT_SIN_PRI": "09/03/2026",
                "HOSPITAL": "1",
                "UTI": "2",
                "EVOLUCAO": "1",
            },
            {
                "SG_UF": "MT",
                "CO_MUN_RES": "510840",
                "SEM_PRI": "202612",
                "DT_SIN_PRI": "16/03/2026",
                "HOSPITAL": "1",
                "UTI": "1",
                "EVOLUCAO": "1",
            },
            {
                "SG_UF": "SP",
                "CO_MUN_RES": "355030",
                "SEM_PRI": "202612",
                "DT_SIN_PRI": "16/03/2026",
                "HOSPITAL": "1",
                "UTI": "1",
                "EVOLUCAO": "2",
            },
        ]
        pd.DataFrame(rows).to_csv(path, sep=";", index=False)

    def test_end_to_end_mt_aggregation(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            population = root / "population.csv"
            config = root / "config.json"
            sivep = root / "sivep.csv"

            self.make_population(population)
            self.make_config(config)
            self.make_sivep(sivep)

            weekly, municipal, metadata = build_mt_aggregates(sivep, population, config)

            self.assertEqual(metadata["source_rows"], 4)
            self.assertEqual(metadata["mt_residence_rows"], 3)
            self.assertEqual(metadata["municipality_count"], 142)
            self.assertEqual(metadata["max_observed_week"], 12)
            self.assertEqual(metadata["stable_week_provisional"], 10)

            cuiaba = municipal.loc[municipal["codigo_ibge"] == "5103403"].iloc[0]
            vg = municipal.loc[municipal["codigo_ibge"] == "5108402"].iloc[0]

            self.assertEqual(int(cuiaba["casos"]), 2)
            self.assertEqual(int(cuiaba["hospitalizacoes"]), 2)
            self.assertEqual(int(cuiaba["uti"]), 1)
            self.assertEqual(int(cuiaba["obitos"]), 1)
            self.assertEqual(int(cuiaba["curas"]), 1)

            self.assertEqual(int(vg["casos"]), 1)
            self.assertEqual(int(vg["uti"]), 1)

            self.assertEqual(int(weekly["casos"].sum()), 3)
            self.assertEqual(int(weekly["obitos"].sum()), 1)


if __name__ == "__main__":
    unittest.main()
