# -*- coding: utf-8 -*-
import unittest

import pandas as pd

from src.deployment_verification_v2_12 import (
    validate_deployment_records,
    validate_effect_verification_records,
    validate_human_deploy_decisions,
)


CONFIG = {
    "allowed_release_gate_decision": "eligible_for_human_deploy",
    "deploy_decisions": [
        "approve_human_deploy",
        "reject_deploy",
        "defer_deploy",
    ],
    "deployment_states": [
        "verified_healthy",
        "needs_investigation",
        "rollback_consideration",
    ],
    "verification_statuses": ["passed", "failed", "not_applicable"],
    "rollback_readiness_statuses": ["ready", "blocked", "not_applicable"],
    "effect_states": [
        "implementation_behavior_verified",
        "no_material_behavior_change",
        "unexpected_behavior_needs_review",
        "insufficient_observation_window",
    ],
}


class DeploymentVerificationV212Tests(unittest.TestCase):
    def release_gate(self, decision="eligible_for_human_deploy"):
        return pd.DataFrame([{
            "release_gate_record_id": "releasegate_1",
            "post_merge_record_id": "postmerge_1",
            "implementation_package_id": "implpkg_1",
            "release_commit_sha": "3" * 40,
            "target_environment": "prd",
            "final_release_decision": decision,
            "deploy_eligibility_is_not_deploy": True,
            "automatic_deploy_enabled": False,
            "automatic_rollback_enabled": False,
            "human_deploy_required": True,
        }])

    def deploy_decision(self, decision="approve_human_deploy"):
        return pd.DataFrame([{
            "release_gate_record_id": "releasegate_1",
            "decided_at": "2026-09-27T15:00:00Z",
            "reviewer_role": "revisor_deploy",
            "deploy_decision": decision,
            "decision_rationale": "Deploy revisado e aprovado manualmente.",
        }])

    def deployment(self):
        return pd.DataFrame([{
            "deploy_decision_record_id": "placeholder",
            "deployed_at": "2026-09-27T16:00:00Z",
            "reviewer_role": "revisor_deploy",
            "environment": "prd",
            "deployed_commit_sha": "3" * 40,
            "deploy_evidence_ref": "release-123",
            "post_deploy_ci_status": "passed",
            "smoke_test_status": "passed",
            "health_check_status": "passed",
            "security_privacy_check_status": "passed",
            "rollback_readiness_status": "ready",
            "deployment_state": "verified_healthy",
            "deployment_notes": "Deploy verificado manualmente.",
        }])

    def decisions(self, decision="approve_human_deploy"):
        return validate_human_deploy_decisions(
            self.deploy_decision(decision),
            self.release_gate(),
            CONFIG,
        )

    def test_deploy_decision_requires_release_gate(self):
        out = self.decisions()
        row = out.iloc[0]
        self.assertTrue(bool(row["release_gate_required"]))
        self.assertEqual(row["target_environment"], "prd")
        self.assertEqual(row["release_commit_sha"], "3" * 40)
        self.assertTrue(bool(row["deploy_decision_is_not_deploy_execution"]))
        self.assertFalse(bool(row["automatic_deploy_enabled"]))
        self.assertFalse(bool(row["automatic_rollback_enabled"]))

    def test_noneligible_release_gate_is_rejected(self):
        with self.assertRaises(ValueError):
            validate_human_deploy_decisions(
                self.deploy_decision(),
                self.release_gate("blocked"),
                CONFIG,
            )

    def test_deployment_requires_approved_decision(self):
        decisions = self.decisions("reject_deploy")
        record = self.deployment()
        record.loc[0, "deploy_decision_record_id"] = decisions.iloc[0][
            "deploy_decision_record_id"
        ]
        with self.assertRaises(ValueError):
            validate_deployment_records(record, decisions, CONFIG)

    def test_deployed_commit_must_match_release_commit(self):
        decisions = self.decisions()
        record = self.deployment()
        record.loc[0, "deploy_decision_record_id"] = decisions.iloc[0][
            "deploy_decision_record_id"
        ]
        record.loc[0, "deployed_commit_sha"] = "4" * 40
        with self.assertRaises(ValueError):
            validate_deployment_records(record, decisions, CONFIG)

    def test_environment_must_match_authorized_target(self):
        decisions = self.decisions()
        record = self.deployment()
        record.loc[0, "deploy_decision_record_id"] = decisions.iloc[0][
            "deploy_decision_record_id"
        ]
        record.loc[0, "environment"] = "hml"
        with self.assertRaises(ValueError):
            validate_deployment_records(record, decisions, CONFIG)

    def test_invalid_rollback_readiness_is_rejected(self):
        decisions = self.decisions()
        record = self.deployment()
        record.loc[0, "deploy_decision_record_id"] = decisions.iloc[0][
            "deploy_decision_record_id"
        ]
        record.loc[0, "rollback_readiness_status"] = "maybe"
        with self.assertRaises(ValueError):
            validate_deployment_records(record, decisions, CONFIG)

    def test_effect_verification_is_not_causal_inference(self):
        decisions = self.decisions()
        record = self.deployment()
        record.loc[0, "deploy_decision_record_id"] = decisions.iloc[0][
            "deploy_decision_record_id"
        ]
        deployments = validate_deployment_records(record, decisions, CONFIG)
        effect = pd.DataFrame([{
            "deployment_record_id": deployments.iloc[0]["deployment_record_id"],
            "measured_at": "2026-10-05T12:00:00Z",
            "reviewer_role": "epidemiologista",
            "observation_window_start": "2026-09-28T00:00:00Z",
            "observation_window_end": "2026-10-05T00:00:00Z",
            "effect_state": "implementation_behavior_verified",
            "expected_behavior_summary": "Fila aplica a regra revisada.",
            "observed_behavior_summary": "Comportamento técnico observado conforme esperado.",
            "evidence_refs": "workflow-summary;regression-report",
            "effect_review_notes": "Sem inferência causal sobre desfechos epidemiológicos.",
        }])
        out = validate_effect_verification_records(
            effect, deployments, CONFIG
        )
        row = out.iloc[0]
        self.assertTrue(
            bool(row["effect_verification_is_not_causal_inference"])
        )
        self.assertFalse(bool(row["automatic_rule_change_enabled"]))
        self.assertFalse(bool(row["automatic_rollback_enabled"]))


if __name__ == "__main__":
    unittest.main()
