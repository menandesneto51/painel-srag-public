# -*- coding: utf-8 -*-
import json
import tempfile
import unittest
from pathlib import Path

import pandas as pd

from src.quality_metrics import build_quality_metrics


class QualityMetricsTests(unittest.TestCase):
    def make_population(self, path: Path):
        rows = [
            {"codigo_ibge": "5103403", "municipio": "Cuiabá", "populacao": 700000},
        ]
        used = {"510340"}
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

    def make_config(self, path: Path):
        cfg = {
            "territorial_scope": {
                "residence_uf_field": "SG_UF",
                "residence_uf_value": "MT",
                "municipality_code_candidates": ["CO_MUN_RES"],
            },
            "time": {"symptom_date_field": "DT_SIN_PRI"},
            "severity": {"outcome_field": "EVOLUCAO"},
            "quality": {
                "notification_date_field": "DT_NOTIFIC",
                "digitization_date_field": "DT_DIGITA",
                "closure_date_field": "DT_ENCERRA",
                "final_classification_field": "CLASSI_FIN",
            },
        }
        path.write_text(json.dumps(cfg), encoding="utf-8")

    def make_sivep(self, path: Path):
        rows = [
            {
                "SG_UF": "MT",
                "CO_MUN_RES": "510340",
                "DT_SIN_PRI": "01/03/2026",
                "DT_NOTIFIC": "03/03/2026",
                "DT_DIGITA": "04/03/2026",
                "CLASSI_FIN": "1",
                "EVOLUCAO": "1",
                "DT_ENCERRA": "10/03/2026",
            },
            {
                "SG_UF": "MT",
                "CO_MUN_RES": "510340",
                "DT_SIN_PRI": "05/03/2026",
                "DT_NOTIFIC": "08/03/2026",
                "DT_DIGITA": "10/03/2026",
                "CLASSI_FIN": "2",
                "EVOLUCAO": "2",
                "DT_ENCERRA": "12/03/2026",
            },
            {
                "SG_UF": "MT",
                "CO_MUN_RES": "510340",
                "DT_SIN_PRI": "10/03/2026",
                "DT_NOTIFIC": "09/03/2026",
                "DT_DIGITA": "08/03/2026",
                "CLASSI_FIN": "9",
                "EVOLUCAO": "9",
                "DT_ENCERRA": "",
            },
        ]
        pd.DataFrame(rows).to_csv(path, sep=";", index=False)

    def test_quality_metrics_are_separate_and_reproducible(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            pop = root / "population.csv"
            cfg = root / "config.json"
            sivep = root / "sivep.csv"
            self.make_population(pop)
            self.make_config(cfg)
            self.make_sivep(sivep)

            municipal, metadata = build_quality_metrics(sivep, pop, cfg)
            cuiaba = municipal.loc[municipal["codigo_ibge"] == "5103403"].iloc[0]

            self.assertTrue(metadata["risk_separation"])
            self.assertEqual(int(cuiaba["registros"]), 3)
            self.assertAlmostEqual(float(cuiaba["atraso_notificacao_mediana_dias"]), 2.5)
            self.assertAlmostEqual(float(cuiaba["atraso_digitacao_mediana_dias"]), 1.5)
            self.assertAlmostEqual(float(cuiaba["desfecho_completo_percent"]), 66.6666666667, places=5)
            self.assertAlmostEqual(float(cuiaba["encerramento_completo_percent"]), 100.0)
            self.assertEqual(int(cuiaba["inconsistencias_temporais"]), 1)


if __name__ == "__main__":
    unittest.main()
