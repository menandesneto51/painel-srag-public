# -*- coding: utf-8 -*-
import unittest

import pandas as pd

from src.postmortem_learning_v2_14 import validate_postmortem_records


CONFIG = {
    "source_record_types": ["effect", "rollback"],
    "postmortem_statuses": ["draft", "in_review", "closed"],
    "outcome_states": [
        "change_retained",
        "change_reverted",
        "investigation_open",
        "inconclusive",
    ],
    "learning_action_types": [
        "none",
        "documentation",
        "monitoring",
        "testing",
        "runbook",
        "rule_review",
        "data_quality",
        "security_privacy",
    ],
    "rule_review_scopes": [
        "queue_rule",
        "action_trigger",
        "threshold",
        "context_requirement",
        "documentation",
    ],
}


class PostmortemLearningV214Tests(unittest.TestCase):
    def effects(self):
        return pd.DataFrame([{
            "effect_verification_record_id": "effect_1",
            "deployment_record_id": "deploy_1",
            "implementation_package_id": "implpkg_1",
            "deployed_commit_sha": "3" * 40,
            "effect_state": "implementation_behavior_verified",
            "effect_verification_is_not_causal_inference": True,
            "automatic_rule_change_enabled": False,
            "automatic_rollback_enabled": False,
        }])

    def rollbacks(self):
        return pd.DataFrame([{
            "rollback_execution_record_id": "rollback_1",
            "implementation_package_id": "implpkg_1",
            "rolled_back_commit_sha": "2" * 40,
            "rollback_execution_state": "verified_restored",
            "rollback_record_requires_actual_rollback_evidence": True,
            "automatic_rule_change_enabled": False,
            "automatic_rollback_enabled": False,
        }])

    def record(self, source_type="effect", source_id="effect_1"):
        return pd.DataFrame([{
            "source_record_type": source_type,
            "source_record_id": source_id,
            "conducted_at": "2026-10-07T12:00:00Z",
            "reviewer_role": "epidemiologista_senior",
            "postmortem_status": "closed",
            "outcome_state": "change_retained",
            "event_summary": "Mudança revisada após janela observacional.",
            "expected_behavior_summary": "Fila deveria refletir a regra revisada.",
            "observed_behavior_summary": "Comportamento técnico compatível com o esperado.",
            "contributing_factors": "Cobertura de testes e monitoramento adequados.",
            "safeguards_that_worked": "CI, shadow e revisão humana.",
            "safeguards_to_improve": "Ampliar observabilidade.",
            "lessons_learned": "Manter janela observacional explícita.",
            "learning_action_type": "monitoring",
            "follow_up_actions": "Ampliar métricas de observabilidade.",
            "evidence_refs": "effect_1;report",
            "reenter_rule_review": False,
            "rule_review_scope": "",
            "rule_review_reason": "",
        }])

    def test_learning_record_does_not_change_rule(self):
        out = validate_postmortem_records(
            self.record(), self.effects(), self.rollbacks(), CONFIG
        )
        row = out.iloc[0]
        self.assertTrue(bool(row["postmortem_is_not_causal_proof"]))
        self.assertTrue(bool(row["learning_is_not_rule_change"]))
        self.assertFalse(bool(row["automatic_rule_change_enabled"]))
        self.assertFalse(bool(row["automatic_issue_creation_enabled"]))

    def test_rule_review_reentry_requires_scope_and_reason(self):
        record = self.record()
        record.loc[0, "learning_action_type"] = "rule_review"
        record.loc[0, "reenter_rule_review"] = True
        record.loc[0, "rule_review_scope"] = ""
        with self.assertRaises(ValueError):
            validate_postmortem_records(
                record, self.effects(), self.rollbacks(), CONFIG
            )

    def test_rule_review_reentry_is_human_only(self):
        record = self.record()
        record.loc[0, "learning_action_type"] = "rule_review"
        record.loc[0, "reenter_rule_review"] = True
        record.loc[0, "rule_review_scope"] = "threshold"
        record.loc[0, "rule_review_reason"] = "Revisar sensibilidade observada."
        out = validate_postmortem_records(
            record, self.effects(), self.rollbacks(), CONFIG
        )
        row = out.iloc[0]
        self.assertTrue(bool(row["reenter_rule_review"]))
        self.assertTrue(bool(row["rule_reentry_requires_human_review"]))
        self.assertFalse(bool(row["automatic_rule_change_enabled"]))

    def test_closed_postmortem_cannot_leave_investigation_open(self):
        record = self.record()
        record.loc[0, "outcome_state"] = "investigation_open"
        with self.assertRaises(ValueError):
            validate_postmortem_records(
                record, self.effects(), self.rollbacks(), CONFIG
            )

    def test_rollback_can_be_postmortem_source(self):
        record = self.record("rollback", "rollback_1")
        record.loc[0, "outcome_state"] = "change_reverted"
        out = validate_postmortem_records(
            record, self.effects(), self.rollbacks(), CONFIG
        )
        self.assertEqual(
            out.iloc[0]["source_record_type"],
            "rollback",
        )


if __name__ == "__main__":
    unittest.main()
