# -*- coding: utf-8 -*-
import unittest

import pandas as pd

from src.governance_observability_report_v2_16 import (
    build_governance_observability_metadata,
    render_governance_observability_report,
)


class GovernanceObservabilityReportV216Tests(unittest.TestCase):
    def status(self):
        return pd.DataFrame([
            {
                "proposal_id": "p1",
                "current_stage": "merge_gate",
                "stale_experimental": True,
                "terminal_stage": False,
                "hours_since_last_event": 96.0,
                "stale_threshold_hours": 72.0,
                "stale_flag_is_not_risk": True,
                "reviewer_score_enabled": False,
                "municipality_rank_enabled": False,
                "automatic_action_enabled": False,
            },
            {
                "proposal_id": "p2",
                "current_stage": "effect_verification",
                "stale_experimental": False,
                "terminal_stage": True,
                "hours_since_last_event": 400.0,
                "stale_threshold_hours": 336.0,
                "stale_flag_is_not_risk": True,
                "reviewer_score_enabled": False,
                "municipality_rank_enabled": False,
                "automatic_action_enabled": False,
            },
        ])

    def transitions(self):
        return pd.DataFrame([
            {
                "event_type": "merge_gate",
                "transition_hours": 24.0,
                "duration_status": "computed",
            }
        ])

    def test_metadata_preserves_non_scoring_governance(self):
        meta = build_governance_observability_metadata(
            self.status(),
            self.transitions(),
        )
        self.assertFalse(meta["reviewer_scoring"])
        self.assertFalse(meta["municipality_ranking"])
        self.assertFalse(meta["thresholds_are_institutional_sla"])
        self.assertEqual(
            meta["threshold_status"],
            "experimental_internal_not_sla",
        )

    def test_report_explicitly_rejects_performance_scoring(self):
        report = render_governance_observability_report(
            self.status(),
            self.transitions(),
        )
        self.assertIn("não de desempenho individual", report)
        self.assertIn("não constituem SLA da SES", report)
        self.assertIn("não representam risco epidemiológico", report)


if __name__ == "__main__":
    unittest.main()
