# -*- coding: utf-8 -*-
import unittest

import pandas as pd

from src.learning_action_followup_v2_17 import (
    validate_learning_action_followup,
)


CONFIG = {
    "eligible_postmortem_statuses": ["in_review", "closed"],
    "action_statuses": [
        "planned", "acknowledged", "in_progress",
        "blocked", "completed", "cancelled",
    ],
    "verification_statuses": [
        "not_started", "pending", "verified",
        "rejected", "not_applicable",
    ],
}


class LearningActionFollowupV217Tests(unittest.TestCase):
    def postmortems(self, action_type="monitoring"):
        return pd.DataFrame([{
            "postmortem_record_id": "postmortem_1",
            "implementation_package_id": "implpkg_1",
            "conducted_at": "2026-10-01T12:00:00Z",
            "postmortem_status": "closed",
            "learning_action_type": action_type,
            "follow_up_actions": "Acompanhar comportamento por 30 dias.",
            "reenter_rule_review": action_type == "rule_review",
            "rule_review_scope": "threshold" if action_type == "rule_review" else "",
            "rule_review_reason": "Revisar sensibilidade." if action_type == "rule_review" else "",
            "postmortem_is_not_causal_proof": True,
            "learning_is_not_rule_change": True,
            "rule_reentry_requires_human_review": True,
            "automatic_rule_change_enabled": False,
            "automatic_issue_creation_enabled": False,
        }])

    def action(self):
        return pd.DataFrame([{
            "postmortem_record_id": "postmortem_1",
            "action_sequence": 1,
            "action_description": "Acompanhar comportamento por 30 dias.",
            "owner_role": "epidemiologia",
            "created_at": "2026-10-02T12:00:00Z",
            "due_at": "2026-11-01T12:00:00Z",
            "action_status": "in_progress",
            "status_updated_at": "2026-10-10T12:00:00Z",
            "completed_at": "",
            "completion_evidence_refs": "",
            "verification_status": "not_started",
            "verified_at": "",
            "verifier_role": "",
            "verification_notes": "",
            "blocking_reason": "",
            "cancellation_rationale": "",
            "governance_handoff_ref": "",
        }])

    def test_open_action_is_not_execution(self):
        out = validate_learning_action_followup(
            self.action(), self.postmortems(), CONFIG,
            "2026-10-15T12:00:00Z",
        )
        row = out.iloc[0]
        self.assertEqual(row["follow_up_state"], "open")
        self.assertFalse(bool(row["overdue"]))
        self.assertTrue(bool(row["tracking_is_not_execution"]))
        self.assertFalse(bool(row["automatic_execution_enabled"]))

    def test_overdue_is_workflow_not_risk(self):
        out = validate_learning_action_followup(
            self.action(), self.postmortems(), CONFIG,
            "2026-11-05T12:00:00Z",
        )
        row = out.iloc[0]
        self.assertEqual(row["follow_up_state"], "overdue")
        self.assertTrue(bool(row["overdue"]))
        self.assertTrue(bool(row["overdue_is_not_risk"]))

    def test_completed_requires_evidence(self):
        action = self.action()
        action.loc[0, "action_status"] = "completed"
        action.loc[0, "status_updated_at"] = "2026-10-20T12:00:00Z"
        action.loc[0, "completed_at"] = "2026-10-20T11:00:00Z"
        action.loc[0, "verification_status"] = "pending"
        with self.assertRaises(ValueError):
            validate_learning_action_followup(
                action, self.postmortems(), CONFIG,
                "2026-10-21T12:00:00Z",
            )

    def test_verified_completion_is_not_effectiveness_proof(self):
        action = self.action()
        action.loc[0, "action_status"] = "completed"
        action.loc[0, "status_updated_at"] = "2026-10-21T12:00:00Z"
        action.loc[0, "completed_at"] = "2026-10-20T11:00:00Z"
        action.loc[0, "completion_evidence_refs"] = "report:monitoring-30d"
        action.loc[0, "verification_status"] = "verified"
        action.loc[0, "verified_at"] = "2026-10-21T11:00:00Z"
        action.loc[0, "verifier_role"] = "revisao_epidemiologica"
        action.loc[0, "verification_notes"] = "Evidência conferida."
        out = validate_learning_action_followup(
            action, self.postmortems(), CONFIG,
            "2026-10-22T12:00:00Z",
        )
        row = out.iloc[0]
        self.assertEqual(row["follow_up_state"], "verified_closed")
        self.assertTrue(bool(row["completion_is_not_effectiveness_proof"]))
        self.assertTrue(bool(row["verification_is_not_epidemiological_effect"]))

    def test_rule_review_completion_requires_governance_handoff(self):
        action = self.action()
        action.loc[0, "action_status"] = "completed"
        action.loc[0, "status_updated_at"] = "2026-10-21T12:00:00Z"
        action.loc[0, "completed_at"] = "2026-10-20T11:00:00Z"
        action.loc[0, "completion_evidence_refs"] = "review:threshold"
        action.loc[0, "verification_status"] = "pending"
        with self.assertRaises(ValueError):
            validate_learning_action_followup(
                action, self.postmortems("rule_review"), CONFIG,
                "2026-10-22T12:00:00Z",
            )

    def test_personal_identifier_columns_are_rejected(self):
        action = self.action()
        action["owner_name"] = "Pessoa"
        with self.assertRaises(ValueError):
            validate_learning_action_followup(
                action, self.postmortems(), CONFIG,
                "2026-10-15T12:00:00Z",
            )


if __name__ == "__main__":
    unittest.main()
