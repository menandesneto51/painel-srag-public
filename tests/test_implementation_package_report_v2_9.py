# -*- coding: utf-8 -*-
import unittest

import pandas as pd

from src.implementation_package_report_v2_9 import (
    render_implementation_package_report,
    summarize_implementation_packages,
)


class ImplementationPackageReportV29Tests(unittest.TestCase):
    def frame(self):
        return pd.DataFrame([{
            "implementation_package_id": "implpkg_1",
            "proposal_id": "prop_1",
            "evaluation_record_id": "eval_1",
            "proposal_type": "queue_rule",
            "rule_key": "review_queue::epidemiology_review",
            "created_at": "2026-09-27T12:00:00Z",
            "package_status": "ready_for_manual_branch",
            "target_branch_suggestion": "change/prop_1",
            "target_paths": "config/operational_review_v2_2.json",
            "required_tests": "unit|regression|backtest",
            "acceptance_criteria": "CI verde.",
            "rollback_plan": "Reverter commit.",
            "package_is_not_implementation": True,
            "manual_branch_required": True,
            "automatic_branch_creation_enabled": False,
            "automatic_code_edit_enabled": False,
            "automatic_commit_enabled": False,
            "automatic_merge_enabled": False,
            "automatic_deploy_enabled": False,
            "human_review_required": True,
        }])

    def test_summary_preserves_manual_only_workflow(self):
        summary = summarize_implementation_packages(self.frame())
        self.assertTrue(summary["manual_branch_required"])
        self.assertFalse(summary["automatic_branch_creation"])
        self.assertFalse(summary["automatic_code_edit"])
        self.assertFalse(summary["automatic_commit"])
        self.assertFalse(summary["automatic_merge"])
        self.assertFalse(summary["automatic_deploy"])

    def test_report_states_package_is_not_implementation(self):
        report = render_implementation_package_report(self.frame())
        self.assertIn("Pacote não é implementação", report)
        self.assertIn("nenhum merge/deploy ocorre automaticamente", report)


if __name__ == "__main__":
    unittest.main()
