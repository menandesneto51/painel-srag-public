# -*- coding: utf-8 -*-
import unittest

import pandas as pd

from src.human_workflow_concordance_report_v2_6 import (
    build_concordance_metadata,
    render_concordance_report,
)


class ConcordanceReportV26Tests(unittest.TestCase):
    def frame(self):
        return pd.DataFrame([
            {
                "decision_record_id": "d1",
                "review_queue": "epidemiology_review",
                "decision_status": "continue_monitoring",
                "workflow_alignment": "nonroutine_not_escalated_rule_review",
                "rule_review_required": True,
                "reviewer_score_enabled": False,
                "municipality_rank_enabled": False,
            },
            {
                "decision_record_id": "d2",
                "review_queue": "routine_monitoring",
                "decision_status": "continue_monitoring",
                "workflow_alignment": "routine_non_escalation_aligned",
                "rule_review_required": False,
                "reviewer_score_enabled": False,
                "municipality_rank_enabled": False,
            },
        ])

    def test_metadata_never_scores_reviewer(self):
        metadata = build_concordance_metadata(self.frame())
        self.assertEqual(metadata["rule_review_records"], 1)
        self.assertFalse(metadata["reviewer_scoring"])
        self.assertFalse(metadata["municipality_ranking"])
        self.assertFalse(metadata["automatic_rule_change"])

    def test_report_targets_rule_not_human(self):
        report = render_concordance_report(self.frame())
        self.assertIn("Discordância não significa erro humano", report)
        self.assertIn("Nenhuma regra é reescrita automaticamente", report)


if __name__ == "__main__":
    unittest.main()
