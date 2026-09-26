# -*- coding: utf-8 -*-
import unittest

from src.risk_model import publication_ready, rate_per_100k, smoothed_proportion, trend_ratio


class RiskModelTests(unittest.TestCase):
    def test_rate_per_100k(self):
        signal = rate_per_100k(10, 100_000)
        self.assertEqual(signal.status, "ok")
        self.assertAlmostEqual(signal.value, 10.0)

    def test_rate_rejects_invalid_population(self):
        signal = rate_per_100k(1, 0)
        self.assertEqual(signal.status, "invalid")
        self.assertIsNone(signal.value)

    def test_smoothing_reduces_small_denominator_extreme(self):
        signal = smoothed_proportion(1, 1, statewide_rate=0.20, prior_strength=10)
        self.assertEqual(signal.status, "experimental")
        self.assertGreater(signal.value, 0.20)
        self.assertLess(signal.value, 1.0)

    def test_trend_ratio_handles_zero_previous(self):
        signal = trend_ratio(3, 0)
        self.assertEqual(signal.status, "experimental")
        self.assertGreater(signal.value, 1.0)

    def test_publication_ready_requires_all_gates(self):
        self.assertTrue(publication_ready("validated", True, True))
        self.assertFalse(publication_ready("under_calibration", True, True))
        self.assertFalse(publication_ready("validated", False, True))


if __name__ == "__main__":
    unittest.main()
