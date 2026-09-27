# -*- coding: utf-8 -*-
import unittest

import pandas as pd

from src.merge_gate_report_v2_10 import (
    render_merge_gate_report,
    summarize_merge_gate,
)


class MergeGateReportV210Tests(unittest.TestCase):
    def frame(self):
        return pd.DataFrame([{
            "merge_gate_record_id": "mergegate_1",
            "implementation_package_id": "implpkg_1",
            "proposal_id": "prop_1",
            "proposal_type": "queue_rule",
            "evaluated_at": "2026-09-27T13:00:00Z",
            "implementation_branch": "change/prop_1",
            "source_commit_sha": "1" * 40,
            "implementation_commit_sha": "2" * 40,
            "changed_paths": "config/operational_review_v2_2.json",
            "diff_review_status": "passed",
            "scope_review_status": "passed",
            "ci_status": "passed",
            "regression_tests_status": "passed",
            "backtest_status": "passed",
            "epidemiology_revalidation_status": "passed",
            "statistical_revalidation_status": "passed",
            "security_privacy_review_status": "passed",
            "acceptance_criteria_status": "passed",
            "rollback_verification_status": "passed",
            "final_gate_decision": "eligible_for_human_merge",
            "gate_rationale": "Todos os gates aprovados.",
            "merge_eligibility_is_not_merge": True,
            "automatic_commit_enabled": False,
            "automatic_merge_enabled": False,
            "automatic_deploy_enabled": False,
            "human_merge_required": True,
            "human_review_required": True,
        }])

    def test_summary_preserves_human_only_merge(self):
        summary = summarize_merge_gate(self.frame())
        self.assertTrue(summary["merge_eligibility_is_not_merge"])
        self.assertFalse(summary["automatic_commit"])
        self.assertFalse(summary["automatic_merge"])
        self.assertFalse(summary["automatic_deploy"])
        self.assertTrue(summary["human_merge_required"])

    def test_report_states_eligibility_is_not_merge(self):
        report = render_merge_gate_report(self.frame())
        self.assertIn("Elegível para merge humano não significa merge executado", report)
        self.assertIn("ações explícitas e separadas", report)


if __name__ == "__main__":
    unittest.main()
