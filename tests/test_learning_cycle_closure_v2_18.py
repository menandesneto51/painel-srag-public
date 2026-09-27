# -*- coding: utf-8 -*-
import unittest

import pandas as pd

from src.learning_cycle_closure_v2_18 import (
    validate_learning_cycle_closure,
)


CONFIG = {
    "eligible_postmortem_statuses": ["closed"],
    "terminal_action_states": ["verified_closed", "cancelled"],
    "blocking_action_states": [
        "open", "overdue", "blocked", "blocked_overdue",
        "completed_pending_verification", "verification_rejected",
    ],
    "review_statuses": ["passed", "failed", "not_applicable"],
    "closure_decisions": [
        "close_learning_cycle", "keep_open", "defer"
    ],
}


class LearningCycleClosureV218Tests(unittest.TestCase):
    def postmortems(self, action_type="monitoring"):
        return pd.DataFrame([{
            "postmortem_record_id": "postmortem_1",
            "implementation_package_id": "implpkg_1",
            "conducted_at": "2026-10-01T12:00:00Z",
            "postmortem_status": "closed",
            "learning_action_type": action_type,
            "reenter_rule_review": action_type == "rule_review",
            "postmortem_is_not_causal_proof": True,
            "learning_is_not_rule_change": True,
            "automatic_rule_change_enabled": False,
            "automatic_issue_creation_enabled": False,
        }])

    def actions(self, state="verified_closed", action_type="monitoring"):
        return pd.DataFrame([{
            "learning_action_record_id": "action_1",
            "postmortem_record_id": "postmortem_1",
            "learning_action_type": action_type,
            "follow_up_state": state,
            "as_of": "2026-10-25T12:00:00Z",
            "governance_handoff_ref": (
                "governance:rule-review-1"
                if action_type == "rule_review" and state == "verified_closed"
                else ""
            ),
            "tracking_is_not_execution": True,
            "completion_is_not_effectiveness_proof": True,
            "overdue_is_not_risk": True,
            "automatic_execution_enabled": False,
            "automatic_issue_creation_enabled": False,
            "automatic_rule_change_enabled": False,
        }])

    def decision(self, close=True, action_type="monitoring"):
        return pd.DataFrame([{
            "postmortem_record_id": "postmortem_1",
            "evaluated_at": "2026-10-24T12:00:00Z",
            "reviewer_role": "governanca_epidemiologica",
            "action_coverage_review_status": "passed",
            "evidence_review_status": "passed",
            "rule_handoff_review_status": (
                "passed" if action_type == "rule_review"
                else "not_applicable"
            ),
            "closure_decision": (
                "close_learning_cycle" if close else "keep_open"
            ),
            "decision_rationale": "Ações revisadas.",
            "closure_evidence_refs": "review:closure-1" if close else "",
        }])

    def test_human_closure_requires_terminal_actions(self):
        with self.assertRaises(ValueError):
            validate_learning_cycle_closure(
                self.decision(),
                self.postmortems(),
                self.actions("open"),
                CONFIG,
            )

    def test_verified_actions_can_close_cycle(self):
        out = validate_learning_cycle_closure(
            self.decision(),
            self.postmortems(),
            self.actions(),
            CONFIG,
        )
        row = out.iloc[0]
        self.assertEqual(
            row["learning_cycle_state"],
            "learning_cycle_closed_human",
        )
        self.assertTrue(
            bool(row["postmortem_closed_is_not_learning_cycle_closed"])
        )
        self.assertTrue(bool(row["closure_is_not_epidemiological_effect"]))
        self.assertFalse(bool(row["automatic_closure_enabled"]))

    def test_rule_review_requires_handoff(self):
        actions = self.actions(
            "verified_closed", action_type="rule_review"
        )
        actions.loc[0, "governance_handoff_ref"] = ""
        with self.assertRaises(ValueError):
            validate_learning_cycle_closure(
                self.decision(action_type="rule_review"),
                self.postmortems("rule_review"),
                actions,
                CONFIG,
            )

    def test_action_type_must_match_postmortem(self):
        actions = self.actions(action_type="monitoring")
        with self.assertRaises(ValueError):
            validate_learning_cycle_closure(
                self.decision(action_type="rule_review"),
                self.postmortems("rule_review"),
                actions,
                CONFIG,
            )

    def test_keep_open_accepts_blocking_action(self):
        out = validate_learning_cycle_closure(
            self.decision(close=False),
            self.postmortems(),
            self.actions("overdue"),
            CONFIG,
        )
        self.assertEqual(
            out.iloc[0]["learning_cycle_state"],
            "learning_cycle_open",
        )

    def test_action_snapshot_must_not_predate_evaluation(self):
        actions = self.actions()
        actions.loc[0, "as_of"] = "2026-10-20T12:00:00Z"
        with self.assertRaises(ValueError):
            validate_learning_cycle_closure(
                self.decision(),
                self.postmortems(),
                actions,
                CONFIG,
            )


if __name__ == "__main__":
    unittest.main()
