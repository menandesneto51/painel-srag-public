# -*- coding: utf-8 -*-
import unittest

import pandas as pd

from src.deployment_verification_v2_12 import (
    validate_deployment_records,
    validate_effect_verification_records,
    validate_human_deploy_decisions,
)


CONFIG = {
    "allowed_post_merge_states": ["verified_healthy"],
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
    "effect_states": [
        "implementation_behavior_verified",
        "no_material_behavior_change",
        "unexpected_behavior_needs_review",
        "insufficient_observation_window",
    ],
}


class DeploymentVerificationV212Tests(unittest.TestCase):
    def post_merge(self):
        return pd.DataFrame([{
            "post_merge_record_id": "postmerge_1",
            "implementation_package_id": "implpkg_1",
            "merged_commit_sha": "3" * 40,
            "post_merge_state": "verified_healthy",
            "post_merge_record_is_not_deploy": True,
            "automatic_deploy_enabled": False,
            "automatic_rollback_enabled": False,
        }])

    def deploy_decision(self, decision="approve_human_deploy"):
        return pd.DataFrame([{
            "post_merge_record_id": "postmerge_1",
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
            "environment": "production",
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

    def test_deploy_decision_does_not_execute_deploy(self):
        out = validate_human_deploy_decisions(
            self.deploy_decision(), self.post_merge(), CONFIG
        )
        row = out.iloc[0]
        self.assertTrue(bool(row["deploy_decision_is_not_deploy_execution"]))
        self.assertFalse(bool(row["automatic_deploy_enabled"]))
        self.assertFalse(bool(row["automatic_rollback_enabled"]))

    def test_deployment_requires_approved_decision(self):
        decisions = validate_human_deploy_decisions(
            self.deploy_decision("reject_deploy"), self.post_merge(), CONFIG
        )
        record = self.deployment()
        record.loc[0, "deploy_decision_record_id"] = decisions.iloc[0][
            "deploy_decision_record_id"
        ]
        with self.assertRaises(ValueError):
            validate_deployment_records(record, decisions, CONFIG)

    def test_deployed_commit_must_match_merged_commit(self):
        decisions = validate_human_deploy_decisions(
            self.deploy_decision(), self.post_merge(), CONFIG
        )
        record = self.deployment()
        record.loc[0, "deploy_decision_record_id"] = decisions.iloc[0][
            "deploy_decision_record_id"
        ]
        record.loc[0, "deployed_commit_sha"] = "4" * 40
        with self.assertRaises(ValueError):
            validate_deployment_records(record, decisions, CONFIG)

    def test_effect_verification_is_not_causal_inference(self):
        decisions = validate_human_deploy_decisions(
            self.deploy_decision(), self.post_merge(), CONFIG
        )
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
