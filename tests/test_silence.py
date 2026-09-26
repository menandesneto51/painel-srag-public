# -*- coding: utf-8 -*-
import unittest

from src.silence import classify_silence, derive_reporting_evidence


class SilenceTests(unittest.TestCase):
    def test_zero_expected_is_compatible_absence(self):
        result = classify_silence(
            observed_cases=0,
            baseline_median=0,
            baseline_q75=0,
            baseline_n_years=4,
            reporting_evidence="unknown",
            data_quality_class="low",
            regional_signal_status=None,
        )
        self.assertEqual(result["silence_class"], "absence_compatible_with_expected")

    def test_zero_with_expected_activity_and_weak_reporting_is_data_gap(self):
        result = classify_silence(
            observed_cases=0,
            baseline_median=3,
            baseline_q75=5,
            baseline_n_years=4,
            reporting_evidence="none",
            data_quality_class="insufficient",
            regional_signal_status=None,
        )
        self.assertEqual(result["silence_class"], "data_quality_or_reporting_gap")

    def test_priority_requires_context_not_zero_alone(self):
        result = classify_silence(
            observed_cases=0,
            baseline_median=4,
            baseline_q75=6,
            baseline_n_years=5,
            reporting_evidence="recent_reporting_activity",
            data_quality_class="high",
            regional_signal_status="persistent_elevated",
            priority_expected_median=2,
        )
        self.assertEqual(result["silence_class"], "silence_priority_candidate")
        self.assertTrue(result["priority_candidate"])

    def test_nonzero_is_not_silent(self):
        result = classify_silence(
            observed_cases=1,
            baseline_median=4,
            baseline_q75=6,
            baseline_n_years=5,
            reporting_evidence="none",
            data_quality_class="low",
            regional_signal_status="persistent_elevated",
        )
        self.assertEqual(result["silence_class"], "not_silent")

    def test_reporting_evidence_proxy(self):
        self.assertEqual(
            derive_reporting_evidence(prior_window_records=3),
            "recent_reporting_activity",
        )
        self.assertEqual(
            derive_reporting_evidence(explicit_zero_report=True, prior_window_records=0),
            "explicit_zero_report",
        )


if __name__ == "__main__":
    unittest.main()
