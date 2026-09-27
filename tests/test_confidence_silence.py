# -*- coding: utf-8 -*-
import unittest

import pandas as pd

from src.signal_confidence import build_signal_confidence
from src.silence_signals import build_silence_signals


class ConfidenceAndSilenceTests(unittest.TestCase):
    def signals(self):
        return pd.DataFrame([{
            "codigo_ibge": "5103403",
            "municipio": "Cuiabá",
            "SE": 10,
            "baseline_status": "experimental",
            "trend_status": "experimental",
            "anomaly_status": "within_expected_experimental",
        }])

    def quality(self):
        return pd.DataFrame([{
            "codigo_ibge": "5103403",
            "quality_status": "observed",
            "atraso_notificacao_mediana_dias": 3.0,
            "desfecho_completo_percent": 95.0,
            "inconsistencia_temporal_percent": 0.5,
        }])

    def thresholds(self):
        return {
            "notification_delay_high_max_days": 7,
            "notification_delay_moderate_max_days": 14,
            "outcome_complete_high_min_percent": 90,
            "outcome_complete_moderate_min_percent": 75,
            "temporal_inconsistency_high_max_percent": 1,
            "temporal_inconsistency_moderate_max_percent": 5,
        }

    def test_high_confidence_requires_good_quality_and_complete_signal(self):
        out = build_signal_confidence(
            self.signals(), self.quality(), 10, self.thresholds()
        )
        self.assertEqual(out.iloc[0]["signal_confidence"], "high_experimental")
        self.assertTrue(bool(out.iloc[0]["risk_separation"]))

    def test_bad_timeliness_lowers_confidence(self):
        quality = self.quality()
        quality.loc[0, "atraso_notificacao_mediana_dias"] = 30
        out = build_signal_confidence(
            self.signals(), quality, 10, self.thresholds()
        )
        self.assertEqual(out.iloc[0]["signal_confidence"], "low_experimental")

    def test_silence_is_not_operational_alert(self):
        current = pd.DataFrame([
            {"codigo_ibge": "5103403", "municipio": "Cuiabá", "SE": 9, "hospitalizacoes": 0},
            {"codigo_ibge": "5103403", "municipio": "Cuiabá", "SE": 10, "hospitalizacoes": 0},
        ])
        baseline = pd.DataFrame([
            {
                "codigo_ibge": "5103403",
                "municipio": "Cuiabá",
                "SE": 9,
                "metric": "hospitalizacoes",
                "baseline_status": "experimental",
                "baseline_median": 2.0,
                "historical_nonzero_frequency": 0.8,
            },
            {
                "codigo_ibge": "5103403",
                "municipio": "Cuiabá",
                "SE": 10,
                "metric": "hospitalizacoes",
                "baseline_status": "experimental",
                "baseline_median": 2.0,
                "historical_nonzero_frequency": 0.9,
            },
        ])
        confidence = pd.DataFrame([{
            "codigo_ibge": "5103403",
            "signal_confidence": "high_experimental",
        }])
        out = build_silence_signals(
            current, baseline, confidence, stable_week=10, metric="hospitalizacoes"
        )
        self.assertEqual(out.iloc[0]["silence_status"], "silence_signal_under_review")
        self.assertFalse(bool(out.iloc[0]["validated_for_operational_alert"]))


if __name__ == "__main__":
    unittest.main()
