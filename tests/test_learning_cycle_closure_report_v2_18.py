# -*- coding: utf-8 -*-
import unittest

import pandas as pd

from src.learning_cycle_closure_report_v2_18 import (
    build_learning_cycle_closure_summary,
    render_learning_cycle_closure_report,
)


class LearningCycleClosureReportV218Tests(unittest.TestCase):
    def frame(self):
        return pd.DataFrame([{
            "learning_closure_record_id": "c1",
            "learning_cycle_state": "learning_cycle_closed_human",
            "all_actions_terminal": True,
            "learning_action_type": "monitoring",
            "postmortem_closed_is_not_learning_cycle_closed": True,
            "closure_is_not_epidemiological_effect": True,
            "automatic_closure_enabled": False,
            "automatic_issue_creation_enabled": False,
            "automatic_rule_change_enabled": False,
        }])

    def test_summary(self):
        summary = build_learning_cycle_closure_summary(self.frame())
        self.assertEqual(summary["records"], 1)
        self.assertEqual(summary["learning_cycle_closed_human"], 1)
        self.assertFalse(summary["automatic_closure_enabled"])

    def test_report_separates_postmortem_from_learning_closure(self):
        report = render_learning_cycle_closure_report(
            build_learning_cycle_closure_summary(self.frame())
        )
        self.assertIn(
            "Post-mortem fechado não significa ciclo de aprendizado encerrado",
            report,
        )
        self.assertIn("não prova efetividade", report)


if __name__ == "__main__":
    unittest.main()
