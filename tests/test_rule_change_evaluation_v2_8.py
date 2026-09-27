# -*- coding: utf-8 -*-
import unittest

import pandas as pd

from pathlib import Path

from src.rule_change_evaluation_v2_8 import (
    load_evaluation_config,
    validate_rule_change_evaluations,
)


CONFIG = {
    "review_statuses": [
        "not_started",
        "in_progress",
        "passed",
        "failed",
        "not_applicable",
    ],
    "final_decisions": [
        "approve_for_implementation_branch",
        "reject",
        "defer",
    ],
    "logic_change_types": [
        "queue_rule",
        "action_trigger",
        "threshold",
        "context_requirement",
    ],
    "documentation_only_types": ["documentation"],
}


class RuleChangeEvaluationV28Tests(unittest.TestCase):
    def proposals(self, proposal_type="queue_rule"):
        return pd.DataFrame([{
            "proposal_id": "prop_1",
            "proposal_type": proposal_type,
            "proposal_status": "draft",
            "proposal_is_not_change": True,
            "human_approval_required": True,
        }])

    def evaluation(self, decision="approve_for_implementation_branch"):
        return pd.DataFrame([{
            "proposal_id": "prop_1",
            "evaluated_at": "2026-09-27T10:00:00Z",
            "reviewer_role": "epidemiologista_senior",
            "case_review_status": "passed",
            "epidemiology_review_status": "passed",
            "backtest_status": "passed",
            "statistical_review_status": "passed",
            "documentation_status": "passed",
            "impact_summary": "Impacto esperado documentado.",
            "risk_summary": "Riscos de falso acionamento revisados.",
            "final_decision": decision,
            "decision_rationale": "Evidências suficientes para branch de implementação.",
        }])

    def test_repository_config_is_valid(self):
        root = Path(__file__).resolve().parents[1]
        cfg = load_evaluation_config(
            root / "config" / "rule_change_evaluation_v2_8.json"
        )
        self.assertFalse(cfg["principles"]["automatic_rule_change"])
        self.assertFalse(cfg["principles"]["automatic_merge"])
        self.assertTrue(cfg["principles"]["human_approval_required"])

    def test_approval_requires_all_logic_reviews_passed(self):
        out = validate_rule_change_evaluations(
            self.evaluation(),
            self.proposals(),
            CONFIG,
        )
        row = out.iloc[0]
        self.assertTrue(bool(row["decision_is_not_implementation"]))
        self.assertFalse(bool(row["automatic_rule_change_enabled"]))
        self.assertFalse(bool(row["automatic_threshold_change_enabled"]))
        self.assertFalse(bool(row["automatic_merge_enabled"]))
        self.assertFalse(bool(row["automatic_deploy_enabled"]))

    def test_logic_approval_blocked_without_backtest(self):
        evaluation = self.evaluation()
        evaluation.loc[0, "backtest_status"] = "in_progress"
        with self.assertRaises(ValueError):
            validate_rule_change_evaluations(
                evaluation,
                self.proposals(),
                CONFIG,
            )

    def test_reject_does_not_require_all_reviews_passed(self):
        evaluation = self.evaluation("reject")
        evaluation.loc[0, "backtest_status"] = "failed"
        out = validate_rule_change_evaluations(
            evaluation,
            self.proposals(),
            CONFIG,
        )
        self.assertEqual(out.iloc[0]["final_decision"], "reject")

    def test_documentation_change_allows_not_applicable_backtest(self):
        evaluation = self.evaluation()
        evaluation.loc[0, "backtest_status"] = "not_applicable"
        evaluation.loc[0, "statistical_review_status"] = "not_applicable"
        out = validate_rule_change_evaluations(
            evaluation,
            self.proposals("documentation"),
            CONFIG,
        )
        self.assertEqual(
            out.iloc[0]["final_decision"],
            "approve_for_implementation_branch",
        )


if __name__ == "__main__":
    unittest.main()
