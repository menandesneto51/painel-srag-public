# -*- coding: utf-8 -*-
import unittest

import pandas as pd

from src.human_workflow_concordance_v2_6 import (
    build_human_workflow_concordance,
    classify_workflow_alignment,
    summarize_concordance,
)


CONFIG = {
    "routine_queue": "routine_monitoring",
    "escalation_decisions": ["request_epi_investigation"],
    "non_escalation_decisions": [
        "continue_monitoring",
        "closed_no_escalation",
    ],
}


class HumanWorkflowConcordanceV26Tests(unittest.TestCase):
    def decision(self, queue, decision):
        return pd.DataFrame([{
            "decision_record_id": "dec_1",
            "codigo_ibge": "5103403",
            "municipio": "Cuiabá",
            "snapshot_id": "s1",
            "review_queue": queue,
            "decision_scope": "queue",
            "action_id": "",
            "reviewed_at": "2026-09-27T08:00:00Z",
            "reviewer_role": "epidemiologista",
            "decision_status": decision,
            "decision_recorded_by_human": True,
            "automatic_execution_enabled": False,
        }])

    def test_nonroutine_escalation_is_alignment_not_score(self):
        out = build_human_workflow_concordance(
            self.decision(
                "epidemiology_review",
                "request_epi_investigation",
            ),
            CONFIG,
        )
        row = out.iloc[0]
        self.assertEqual(
            row["workflow_alignment"],
            "nonroutine_escalation_aligned",
        )
        self.assertFalse(bool(row["rule_review_required"]))
        self.assertFalse(bool(row["reviewer_score_enabled"]))
        self.assertFalse(bool(row["municipality_rank_enabled"]))

    def test_nonroutine_no_escalation_flags_rule_review(self):
        out = build_human_workflow_concordance(
            self.decision(
                "epidemiology_review",
                "continue_monitoring",
            ),
            CONFIG,
        )
        row = out.iloc[0]
        self.assertEqual(
            row["workflow_alignment"],
            "nonroutine_not_escalated_rule_review",
        )
        self.assertTrue(bool(row["rule_review_required"]))

    def test_routine_escalation_flags_rule_review(self):
        result = classify_workflow_alignment(
            "routine_monitoring",
            "request_epi_investigation",
            "routine_monitoring",
            {"request_epi_investigation"},
            {"continue_monitoring"},
        )
        self.assertEqual(result, "routine_escalated_rule_review")

    def test_summary_never_scores_reviewer(self):
        out = build_human_workflow_concordance(
            self.decision(
                "epidemiology_review",
                "continue_monitoring",
            ),
            CONFIG,
        )
        summary = summarize_concordance(out)
        self.assertFalse(summary["reviewer_scoring"])
        self.assertFalse(summary["municipality_ranking"])
        self.assertFalse(summary["automatic_rule_change"])


if __name__ == "__main__":
    unittest.main()
