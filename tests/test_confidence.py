# -*- coding: utf-8 -*-
import unittest

from src.confidence import (
    build_confidence_profile,
    classify_numeric,
    overall_confidence,
)


CONFIG = {
    "model_id": "test",
    "version": "test",
    "status": "experimental",
    "required_dimensions": [
        "stability",
        "volume",
        "outcome_completeness",
        "timeliness",
        "temporal_consistency",
    ],
    "thresholds": {
        "volume": {"direction": "higher_better", "high": 20, "moderate": 5, "low": 1},
        "outcome_completeness": {"direction": "higher_better", "high": 90, "moderate": 75, "low": 50},
        "timeliness": {"direction": "lower_better", "high": 2, "moderate": 7, "low": 14},
        "temporal_consistency": {"direction": "lower_better", "high": 1, "moderate": 5, "low": 10},
        "laboratory_coverage": {"direction": "higher_better", "high": 80, "moderate": 60, "low": 40},
        "vintage_depth": {"direction": "higher_better", "high": 3, "moderate": 2, "low": 1},
        "baseline_depth": {"direction": "higher_better", "high": 5, "moderate": 4, "low": 3},
    },
}


class ConfidenceTests(unittest.TestCase):
    def test_directional_thresholds(self):
        self.assertEqual(
            classify_numeric(95, CONFIG["thresholds"]["outcome_completeness"]),
            "high",
        )
        self.assertEqual(
            classify_numeric(8, CONFIG["thresholds"]["timeliness"]),
            "low",
        )

    def test_overall_is_worst_required_dimension(self):
        components = {
            "stability": "high",
            "volume": "high",
            "outcome_completeness": "moderate",
            "timeliness": "high",
            "temporal_consistency": "high",
        }
        self.assertEqual(
            overall_confidence(components, CONFIG["required_dimensions"]),
            "moderate",
        )

    def test_unstable_week_limits_confidence(self):
        profile = build_confidence_profile(
            config=CONFIG,
            is_stable=False,
            volume=100,
            outcome_completeness_percent=99,
            notification_delay_median_days=1,
            temporal_inconsistency_percent=0,
            laboratory_coverage_percent=90,
            vintage_count=3,
            baseline_year_count=5,
        )
        self.assertEqual(profile["confidence_class"], "insufficient")
        self.assertIn("stability", profile["limiting_dimensions"])
        self.assertIsNone(profile["numeric_score"])
        self.assertTrue(profile["risk_separation"])

    def test_high_when_all_required_dimensions_high(self):
        profile = build_confidence_profile(
            config=CONFIG,
            is_stable=True,
            volume=100,
            outcome_completeness_percent=99,
            notification_delay_median_days=1,
            temporal_inconsistency_percent=0,
        )
        self.assertEqual(profile["confidence_class"], "high")


if __name__ == "__main__":
    unittest.main()
