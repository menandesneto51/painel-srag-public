# -*- coding: utf-8 -*-
import unittest

import pandas as pd

from src.human_merge_report_v2_11 import (
    render_human_merge_cycle_report,
    summarize_human_merge_cycle,
)


class HumanMergeReportV211Tests(unittest.TestCase):
    def decisions(self):
        return pd.DataFrame([{
            "merge_decision_record_id": "mergedec_1",
            "merge_decision": "approve_human_merge",
            "merge_decision_is_not_merge_execution": True,
            "automatic_merge_enabled": False,
            "automatic_deploy_enabled": False,
            "automatic_rollback_enabled": False,
            "human_merge_required": True,
        }])

    def post_merge(self):
        return pd.DataFrame([{
            "post_merge_record_id": "postmerge_1",
            "post_merge_state": "verified_healthy",
            "rollback_readiness_status": "ready",
            "post_merge_record_requires_actual_merge_evidence": True,
            "post_merge_record_is_not_deploy": True,
            "automatic_deploy_enabled": False,
            "automatic_rollback_enabled": False,
            "human_post_merge_verification_required": True,
        }])

    def test_summary_preserves_human_only_merge_cycle(self):
        summary = summarize_human_merge_cycle(
            self.decisions(),
            self.post_merge(),
        )
        self.assertFalse(summary["automatic_merge"])
        self.assertFalse(summary["automatic_deploy"])
        self.assertFalse(summary["automatic_rollback"])
        self.assertTrue(summary["human_merge_required"])

    def test_report_separates_merge_and_deploy(self):
        report = render_human_merge_cycle_report(
            self.decisions(),
            self.post_merge(),
        )
        self.assertIn("Decisão de merge não é execução do merge", report)
        self.assertIn("Registro pós-merge não é deploy", report)


if __name__ == "__main__":
    unittest.main()
