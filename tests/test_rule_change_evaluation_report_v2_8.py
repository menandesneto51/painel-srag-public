# -*- coding: utf-8 -*-
import unittest

import pandas as pd

from src.rule_change_evaluation_report_v2_8 import (
    render_rule_change_evaluation_report,
    summarize_rule_change_evaluations,
)


class RuleChangeEvaluationReportV28Tests(unittest.TestCase):
    def frame(self):
        return pd.DataFrame([{
            "evaluation_record_id": "eval_1",
            "proposal_id": "prop_1",
            "proposal_type": "queue_rule",
            "evaluated_at": "2026-09-27T10:00:00Z",
            "reviewer_role": "epidemiologista_senior",
            "case_review_status": "passed",
            "epidemiology_review_status": "passed",
            "backtest_status": "passed",
            "statistical_review_status": "passed",
            "documentation_status": "passed",
            "impact_summary": "Impacto documentado.",
            "risk_summary": "Riscos documentados.",
            "final_decision": "approve_for_implementation_branch",
            "decision_rationale": "Aprovada para branch.",
            "decision_is_not_implementation": True,
            "automatic_rule_change_enabled": False,
            "automatic_threshold_change_enabled": False,
            "automatic_merge_enabled": False,
            "automatic_deploy_enabled": False,
            "human_approval_required": True,
        }])

    def test_summary_preserves_change_control(self):
        summary = summarize_rule_change_evaluations(self.frame())
        self.assertFalse(summary["automatic_rule_change"])
        self.assertFalse(summary["automatic_threshold_change"])
        self.assertFalse(summary["automatic_merge"])
        self.assertFalse(summary["automatic_deploy"])
        self.assertTrue(summary["decision_is_not_implementation"])

    def test_report_states_approval_is_not_implementation(self):
        report = render_rule_change_evaluation_report(self.frame())
        self.assertIn("autoriza apenas preparação de branch", report)
        self.assertIn("não autoriza deploy automático", report)


if __name__ == "__main__":
    unittest.main()
