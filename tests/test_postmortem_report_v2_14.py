# -*- coding: utf-8 -*-
import unittest

import pandas as pd

from src.postmortem_report_v2_14 import (
    build_postmortem_summary,
    render_postmortem_report,
)


class PostmortemReportV214Tests(unittest.TestCase):
    def frame(self):
        return pd.DataFrame([{
            "postmortem_record_id": "p1",
            "source_record_type": "effect",
            "postmortem_status": "closed",
            "outcome_state": "change_retained",
            "learning_action_type": "monitoring",
            "reenter_rule_review": False,
            "postmortem_is_not_causal_proof": True,
            "learning_is_not_rule_change": True,
            "automatic_rule_change_enabled": False,
            "automatic_issue_creation_enabled": False,
        }])

    def test_summary_preserves_governance(self):
        summary = build_postmortem_summary(self.frame())
        self.assertEqual(summary["records"], 1)
        self.assertFalse(summary["automatic_rule_change_enabled"])
        self.assertFalse(summary["automatic_issue_creation_enabled"])

    def test_report_states_learning_is_not_change(self):
        report = render_postmortem_report(
            build_postmortem_summary(self.frame())
        )
        self.assertIn("não altera regras automaticamente", report)
        self.assertIn("não devem ser promovidos automaticamente a conclusões causais", report)


if __name__ == "__main__":
    unittest.main()
