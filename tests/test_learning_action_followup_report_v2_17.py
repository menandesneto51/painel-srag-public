# -*- coding: utf-8 -*-
import unittest

import pandas as pd

from src.learning_action_followup_report_v2_17 import (
    build_learning_action_followup_summary,
    render_learning_action_followup_report,
)


class LearningActionFollowupReportV217Tests(unittest.TestCase):
    def frame(self):
        return pd.DataFrame([{
            "learning_action_record_id": "a1",
            "learning_action_type": "monitoring",
            "action_status": "completed",
            "verification_status": "verified",
            "follow_up_state": "verified_closed",
            "overdue": False,
            "tracking_is_not_execution": True,
            "completion_is_not_effectiveness_proof": True,
            "verification_is_not_epidemiological_effect": True,
            "overdue_is_not_risk": True,
            "automatic_execution_enabled": False,
            "automatic_issue_creation_enabled": False,
            "automatic_rule_change_enabled": False,
        }])

    def test_summary_preserves_governance(self):
        summary = build_learning_action_followup_summary(self.frame())
        self.assertEqual(summary["actions"], 1)
        self.assertEqual(summary["verified_closed"], 1)
        self.assertFalse(summary["automatic_execution_enabled"])
        self.assertFalse(summary["automatic_rule_change_enabled"])

    def test_report_distinguishes_completion_from_effectiveness(self):
        report = render_learning_action_followup_report(
            build_learning_action_followup_summary(self.frame())
        )
        self.assertIn("Conclusão de ação não é prova", report)
        self.assertIn("overdue representa atraso de workflow", report)


if __name__ == "__main__":
    unittest.main()
