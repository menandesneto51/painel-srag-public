# -*- coding: utf-8 -*-
import unittest

import pandas as pd

from src.territorial_review_cards import build_review_cards


class TerritorialReviewCardTests(unittest.TestCase):
    def test_card_is_explainable_and_requires_human_review(self):
        territorial = pd.DataFrame([{
            "codigo_ibge": "5103403",
            "municipio": "Cuiabá",
            "signal_status": "elevated_and_rising_experimental",
            "signal_confidence": "high_experimental",
            "silence_status": "activity_present",
            "virology_status": "named_agent_detected",
            "virology_dominant_agent": "Influenza A",
            "healthcare_pressure_available": False,
            "pressure_status": pd.NA,
            "validation_status": "not_available",
            "territorial_model_status": "under_calibration",
        }])
        card = build_review_cards(territorial).iloc[0]
        self.assertIn("epidemiology_review", card["review_tags"])
        self.assertIn("virology_review", card["review_tags"])
        self.assertIn("Influenza A", card["evidence_summary"])
        self.assertTrue(bool(card["human_review_required"]))
        self.assertFalse(bool(card["operational_recommendation_enabled"]))
        self.assertFalse(bool(card["composite_score_used"]))

    def test_low_confidence_does_not_create_risk_score(self):
        territorial = pd.DataFrame([{
            "codigo_ibge": "5108402",
            "municipio": "Várzea Grande",
            "signal_status": "no_combined_signal_experimental",
            "signal_confidence": "low_experimental",
            "silence_status": "zero_observed_low_confidence",
            "virology_status": "not_available",
            "virology_dominant_agent": pd.NA,
            "healthcare_pressure_available": False,
            "pressure_status": pd.NA,
            "validation_status": "not_available",
            "territorial_model_status": "under_calibration",
        }])
        card = build_review_cards(territorial).iloc[0]
        self.assertIn("data_quality_review", card["review_tags"])
        self.assertFalse(bool(card["composite_score_used"]))


if __name__ == "__main__":
    unittest.main()
