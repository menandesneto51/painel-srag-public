# -*- coding: utf-8 -*-
import unittest

import pandas as pd

from src.anomaly_detection import detect_robust_anomalies, robust_deviation


class AnomalyDetectionTests(unittest.TestCase):
    def test_mad_primary_and_iqr_fallback(self):
        score, method = robust_deviation(20, 10, 2, 8, 12)
        self.assertEqual(method, "MAD")
        self.assertGreater(score, 0)

        score2, method2 = robust_deviation(20, 10, 0, 8, 12)
        self.assertEqual(method2, "IQR")
        self.assertGreater(score2, 0)

        score3, method3 = robust_deviation(20, 10, 0, 10, 10)
        self.assertIsNone(score3)
        self.assertEqual(method3, "NO_DISPERSION")

    def test_persistence_requires_consecutive_weeks(self):
        observed = pd.DataFrame({
            "SE": [1, 2, 3, 4],
            "casos": [10, 40, 45, 10],
        })
        baseline = pd.DataFrame({
            "SE": [1, 2, 3, 4],
            "metric": ["casos"] * 4,
            "n_years": [4] * 4,
            "median": [10.0] * 4,
            "q25": [8.0] * 4,
            "q75": [12.0] * 4,
            "mad": [2.0] * 4,
        })
        result = detect_robust_anomalies(
            observed,
            baseline,
            metric="casos",
            stable_week=4,
            z_threshold=3.5,
            persistence_weeks=2,
            min_baseline_years=3,
        )
        se2 = result.loc[result["SE"] == 2].iloc[0]
        se3 = result.loc[result["SE"] == 3].iloc[0]
        self.assertTrue(bool(se2["candidate_elevated"]))
        self.assertFalse(bool(se2["persistent_elevated"]))
        self.assertTrue(bool(se3["persistent_elevated"]))
        self.assertEqual(se3["signal_status"], "persistent_elevated")

    def test_unstable_weeks_are_excluded(self):
        observed = pd.DataFrame({"SE": [1, 2, 3], "casos": [10, 10, 100]})
        baseline = pd.DataFrame({
            "SE": [1, 2, 3],
            "metric": ["casos"] * 3,
            "n_years": [3] * 3,
            "median": [10.0] * 3,
            "q25": [9.0] * 3,
            "q75": [11.0] * 3,
            "mad": [1.0] * 3,
        })
        result = detect_robust_anomalies(
            observed, baseline, "casos", stable_week=2
        )
        self.assertEqual(result["SE"].tolist(), [1, 2])


if __name__ == "__main__":
    unittest.main()
