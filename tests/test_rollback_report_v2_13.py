# -*- coding: utf-8 -*-
import unittest
import pandas as pd

from src.rollback_report_v2_13 import build_rollback_summary, render_rollback_report


class RollbackReportV213Tests(unittest.TestCase):
    def test_summary_keeps_decision_and_execution_separate(self):
        decisions = pd.DataFrame([{
            "rollback_decision_record_id": "d1",
            "rollback_decision": "approve_human_rollback",
            "rollback_decision_is_not_rollback_execution": True,
            "automatic_rollback_enabled": False,
            "automatic_rule_change_enabled": False,
        }])
        executions = pd.DataFrame([{
            "rollback_execution_record_id": "r1",
            "rollback_execution_state": "verified_restored",
            "rollback_record_requires_actual_rollback_evidence": True,
            "automatic_rollback_enabled": False,
            "automatic_rule_change_enabled": False,
        }])
        summary = build_rollback_summary(decisions, executions)
        self.assertEqual(summary["rollback_decision_records"], 1)
        self.assertEqual(summary["rollback_execution_records"], 1)
        self.assertFalse(summary["automatic_rollback_enabled"])

    def test_report_states_human_governance(self):
        report = render_rollback_report(build_rollback_summary(None, None))
        self.assertIn("decisão humana explícita", report)
        self.assertIn("Alteração automática de regra", report)


if __name__ == "__main__":
    unittest.main()
