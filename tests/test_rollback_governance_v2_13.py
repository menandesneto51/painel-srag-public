# -*- coding: utf-8 -*-
import unittest

import pandas as pd

from src.rollback_governance_v2_13 import (
    validate_human_rollback_decisions,
    validate_rollback_execution_records,
)


CONFIG = {
    "eligible_deployment_states": ["rollback_consideration"],
    "eligible_effect_states": ["unexpected_behavior_needs_review"],
    "rollback_decisions": [
        "approve_human_rollback",
        "reject_rollback",
        "defer_rollback",
    ],
    "rollback_execution_states": [
        "verified_restored",
        "needs_investigation",
    ],
    "verification_statuses": ["passed", "failed", "not_applicable"],
}


class RollbackGovernanceV213Tests(unittest.TestCase):
    def deployments(self):
        return pd.DataFrame([{
            "deployment_record_id": "deploy_1",
            "implementation_package_id": "implpkg_1",
            "deployed_commit_sha": "3" * 40,
            "deployment_state": "rollback_consideration",
            "automatic_rollback_enabled": False,
        }])

    def effects(self):
        return pd.DataFrame([{
            "effect_verification_record_id": "effect_1",
            "deployment_record_id": "deploy_1",
            "implementation_package_id": "implpkg_1",
            "deployed_commit_sha": "3" * 40,
            "effect_state": "unexpected_behavior_needs_review",
            "automatic_rollback_enabled": False,
            "effect_verification_is_not_causal_inference": True,
        }])

    def decision(self, source_type="effect", source_id="effect_1"):
        return pd.DataFrame([{
            "source_record_type": source_type,
            "source_record_id": source_id,
            "decided_at": "2026-10-06T10:00:00Z",
            "reviewer_role": "revisor_rollback",
            "rollback_target_commit_sha": "2" * 40,
            "rollback_plan_ref": "rollback-plan-1",
            "rollback_decision": "approve_human_rollback",
            "decision_rationale": "Comportamento inesperado requer reversão controlada.",
        }])

    def execution(self):
        return pd.DataFrame([{
            "rollback_decision_record_id": "placeholder",
            "rolled_back_at": "2026-10-06T11:00:00Z",
            "reviewer_role": "revisor_rollback",
            "rolled_back_commit_sha": "2" * 40,
            "rollback_evidence_ref": "rollback-event-1",
            "post_rollback_ci_status": "passed",
            "smoke_test_status": "passed",
            "health_check_status": "passed",
            "security_privacy_check_status": "passed",
            "epidemiology_sanity_status": "passed",
            "rollback_execution_state": "verified_restored",
            "verification_notes": "Estado anterior restaurado e verificado.",
        }])

    def test_effect_can_trigger_human_rollback_decision_without_automation(self):
        out = validate_human_rollback_decisions(
            self.decision(),
            self.deployments(),
            self.effects(),
            CONFIG,
        )
        row = out.iloc[0]
        self.assertTrue(
            bool(row["rollback_decision_is_not_rollback_execution"])
        )
        self.assertFalse(bool(row["automatic_rollback_enabled"]))
        self.assertFalse(bool(row["automatic_rule_change_enabled"]))

    def test_noneligible_deployment_cannot_trigger_rollback(self):
        deployments = self.deployments()
        deployments.loc[0, "deployment_state"] = "verified_healthy"
        decision = self.decision("deployment", "deploy_1")
        with self.assertRaises(ValueError):
            validate_human_rollback_decisions(
                decision,
                deployments,
                self.effects(),
                CONFIG,
            )

    def test_execution_requires_approved_target_commit(self):
        decisions = validate_human_rollback_decisions(
            self.decision(),
            self.deployments(),
            self.effects(),
            CONFIG,
        )
        execution = self.execution()
        execution.loc[0, "rollback_decision_record_id"] = decisions.iloc[0][
            "rollback_decision_record_id"
        ]
        out = validate_rollback_execution_records(
            execution,
            decisions,
            CONFIG,
        )
        row = out.iloc[0]
        self.assertEqual(
            row["rollback_execution_state"],
            "verified_restored",
        )
        self.assertTrue(
            bool(row["rollback_record_requires_actual_rollback_evidence"])
        )
        self.assertFalse(bool(row["automatic_rollback_enabled"]))

    def test_wrong_target_commit_is_rejected(self):
        decisions = validate_human_rollback_decisions(
            self.decision(),
            self.deployments(),
            self.effects(),
            CONFIG,
        )
        execution = self.execution()
        execution.loc[0, "rollback_decision_record_id"] = decisions.iloc[0][
            "rollback_decision_record_id"
        ]
        execution.loc[0, "rolled_back_commit_sha"] = "4" * 40
        with self.assertRaises(ValueError):
            validate_rollback_execution_records(
                execution,
                decisions,
                CONFIG,
            )


if __name__ == "__main__":
    unittest.main()
