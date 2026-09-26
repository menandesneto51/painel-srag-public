# -*- coding: utf-8 -*-
import unittest

import pandas as pd

from public_data_validation import has_errors, validate_loaded_data, weekly_value


class ValidationTests(unittest.TestCase):
    def base_payload(self):
        metadata = {"year": 2026, "stable_week": 2, "generated_at": str(pd.Timestamp.now())}
        kpis = {
            "weekly_reference": {"SE_NOTIF": 2, "hospitalizados": 10, "tx_uti_percent": 20.0},
            "weekly_previous": {"SE_NOTIF": 1, "hospitalizados": 8, "tx_uti_percent": 25.0},
        }
        weekly = pd.DataFrame({"ANO_NOTIF": [2026, 2026], "SE_NOTIF": [1, 2]})
        risk = pd.DataFrame({
            "codigo_ibge": [5103403],
            "populacao": [700000],
            "incidencia_100k": [10.0],
            "incidencia_recente_100k": [5.0],
            "tx_uti_percent": [20.0],
            "letalidade_percent": [5.0],
            "score_risco_srag": [50.0],
        })
        forecast = pd.DataFrame({"valor_esperado": [10], "ic95_inf": [5], "ic95_sup": [15]})
        or_table = pd.DataFrame({"OR": [2.0], "IC95% inferior": [1.2], "IC95% superior": [3.3]})
        return metadata, kpis, weekly, risk, forecast, or_table, or_table.copy()

    def valid_candidate(self):
        populations = [3_950_330 - 141] + [1] * 141
        codes = [f"51{i:05d}" for i in range(142)]
        notifications = [0] * 142
        recent = [0] * 142
        return pd.DataFrame({
            "codigo_ibge": codes,
            "NM_MUN": [f"Municipio {i}" for i in range(142)],
            "populacao": populations,
            "notificacoes": notifications,
            "casos_recentes": recent,
            "incidencia_100k": [0.0] * 142,
            "incidencia_recente_100k": [0.0] * 142,
            "score_v2_status": ["blocked"] * 142,
        })

    def test_legacy_aliases_are_read(self):
        record = {"hospitalizados": 10, "tx_uti_percent": 20.0}
        self.assertEqual(weekly_value(record, "hospitalizacoes"), 10)
        self.assertEqual(weekly_value(record, "taxa_uti_hosp_percent"), 20.0)

    def test_stable_week_cannot_exceed_observed_week(self):
        payload = list(self.base_payload())
        payload[0]["stable_week"] = 47
        issues = validate_loaded_data(*payload)
        self.assertTrue(any(i["code"] == "STABLE_WEEK_AFTER_DATA" for i in issues))

    def test_risk_requires_population_and_ibge_code(self):
        payload = list(self.base_payload())
        payload[3] = pd.DataFrame({"NM_MUN": ["Cuiabá"], "incidencia_100k": [100.0]})
        issues = validate_loaded_data(*payload)
        self.assertTrue(any(i["code"] == "MUNICIPAL_CODE_MISSING" for i in issues))
        self.assertTrue(any(i["code"] == "POPULATION_MISSING" for i in issues))
        self.assertTrue(has_errors(issues, {"risk"}))

    def test_invalid_or_interval_is_blocking(self):
        payload = list(self.base_payload())
        payload[5] = pd.DataFrame({"OR": [2.0], "IC95% inferior": [2.5], "IC95% superior": [3.0]})
        issues = validate_loaded_data(*payload)
        self.assertTrue(any(i["code"] == "OR_INTERVAL_INVALID" for i in issues))

    def test_valid_candidate_passes_candidate_gates(self):
        payload = list(self.base_payload())
        candidate = self.valid_candidate()
        issues = validate_loaded_data(*payload, risk_candidate=candidate)
        self.assertFalse(any(i["scope"] == "risk_candidate" and i["severity"] == "error" for i in issues))

    def test_candidate_incidence_must_be_reproducible(self):
        payload = list(self.base_payload())
        candidate = self.valid_candidate()
        candidate.loc[0, "incidencia_100k"] = 1.0
        issues = validate_loaded_data(*payload, risk_candidate=candidate)
        self.assertTrue(any(i["code"] == "INCIDENCE_NOT_REPRODUCIBLE" for i in issues))


if __name__ == "__main__":
    unittest.main()
