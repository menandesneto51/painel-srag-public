# -*- coding: utf-8 -*-
import unittest

import pandas as pd

from src.territorial_intelligence import (
    build_territorial_intelligence,
    summarize_virology_window,
)


class TerritorialIntelligenceTests(unittest.TestCase):
    def test_virology_deduplicates_denominators(self):
        virology = pd.DataFrame([
            {
                "codigo_ibge": "5103403",
                "SE": 10,
                "virus": "Influenza A",
                "deteccoes": 3,
                "registros_srag": 10,
                "pcr_resultado_disponivel": 8,
                "pcr_conclusivo": 7,
                "pcr_detectavel": 4,
            },
            {
                "codigo_ibge": "5103403",
                "SE": 10,
                "virus": "VSR",
                "deteccoes": 1,
                "registros_srag": 10,
                "pcr_resultado_disponivel": 8,
                "pcr_conclusivo": 7,
                "pcr_detectavel": 4,
            },
        ])
        out = summarize_virology_window(virology, stable_week=10, window_weeks=1)
        row = out.iloc[0]
        self.assertEqual(int(row["virology_records_srag"]), 10)
        self.assertEqual(int(row["virology_pcr_result_available"]), 8)
        self.assertEqual(int(row["virology_named_agent_detections"]), 4)
        self.assertEqual(row["virology_dominant_agent"], "Influenza A")

    def test_build_keeps_dimensions_separate_and_no_score(self):
        combined = pd.DataFrame([{
            "codigo_ibge": "5103403",
            "municipio": "Cuiabá",
            "SE": 10,
            "signal_status": "elevated_and_rising_experimental",
            "anomaly_status": "above_expected_experimental",
            "trend_status": "experimental",
            "trend_ratio": 2.0,
            "trend_log2": 1.0,
            "observed_value": 20.0,
            "baseline_median": 8.0,
        }])
        confidence = pd.DataFrame([{
            "codigo_ibge": "5103403",
            "signal_confidence": "high_experimental",
            "confidence_model_status": "under_calibration",
            "risk_separation": True,
        }])
        silence = pd.DataFrame([{
            "codigo_ibge": "5103403",
            "silence_status": "activity_present",
            "silence_model_status": "under_calibration",
        }])
        out = build_territorial_intelligence(
            combined, confidence, silence, stable_week=10
        )
        row = out.iloc[0]
        self.assertEqual(row["signal_confidence"], "high_experimental")
        self.assertEqual(row["virology_status"], "not_available")
        self.assertFalse(bool(row["healthcare_pressure_available"]))
        self.assertTrue(pd.isna(row["composite_score"]))
        self.assertFalse(bool(row["operational_alert"]))


if __name__ == "__main__":
    unittest.main()
