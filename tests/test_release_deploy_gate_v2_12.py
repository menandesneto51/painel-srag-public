# -*- coding: utf-8 -*-
import unittest

import pandas as pd

from src.release_deploy_gate_v2_12 import validate_release_deploy_gate


CONFIG = {
    "allowed_post_merge_state": "verified_healthy",
    "allowed_rollback_readiness": "ready",
    "target_environments": ["hml", "prd"],
    "review_statuses": ["passed", "failed", "not_applicable"],
    "final_release_decisions": [
        "eligible_for_human_deploy",
        "blocked",
        "defer",
    ],
}


class ReleaseDeployGateV212Tests(unittest.TestCase):
    def post_merge(self):
        return pd.DataFrame([{
            "post_merge_record_id": "postmerge_1",
            "merge_decision_record_id": "mergedec_1",
            "merge_gate_record_id": "mergegate_1",
            "implementation_package_id": "implpkg_1",
            "merged_commit_sha": "3" * 40,
            "post_merge_ci_status": "passed",
            "smoke_test_status": "passed",
            "epidemiology_sanity_status": "passed",
            "security_privacy_check_status": "passed",
            "rollback_readiness_status": "ready",
            "post_merge_state": "verified_healthy",
            "post_merge_record_requires_actual_merge_evidence": True,
            "post_merge_record_is_not_deploy": True,
            "automatic_deploy_enabled": False,
            "automatic_rollback_enabled": False,
            "human_post_merge_verification_required": True,
        }])

    def gate(self, decision="eligible_for_human_deploy"):
        return pd.DataFrame([{
            "post_merge_record_id": "postmerge_1",
            "evaluated_at": "2026-09-27T15:00:00Z",
            "reviewer_role": "gestor_release",
            "target_environment": "prd",
            "release_commit_sha": "3" * 40,
            "release_version": "v2.12.0-rc1",
            "release_notes_ref": "docs/release-v2.12.md",
            "deployment_plan_ref": "docs/deploy-v2.12.md",
            "monitoring_plan_ref": "docs/monitoring-v2.12.md",
            "rollback_plan_ref": "docs/rollback-v2.12.md",
            "predeploy_ci_status": "passed",
            "predeploy_security_privacy_status": "passed",
            "monitoring_readiness_status": "passed",
            "rollback_plan_verification_status": "passed",
            "change_window_status": "passed",
            "final_release_decision": decision,
            "release_rationale": "Todos os gates pré-deploy foram aprovados.",
        }])

    def test_eligible_release_is_not_deploy(self):
        out = validate_release_deploy_gate(
            self.gate(),
            self.post_merge(),
            CONFIG,
        )
        row = out.iloc[0]
        self.assertEqual(
            row["final_release_decision"],
            "eligible_for_human_deploy",
        )
        self.assertTrue(bool(row["deploy_eligibility_is_not_deploy"]))
        self.assertFalse(bool(row["automatic_tagging_enabled"]))
        self.assertFalse(bool(row["automatic_deploy_enabled"]))
        self.assertFalse(bool(row["automatic_rollback_enabled"]))
        self.assertTrue(bool(row["human_deploy_required"]))

    def test_release_commit_must_match_verified_merge(self):
        gate = self.gate()
        gate.loc[0, "release_commit_sha"] = "4" * 40
        with self.assertRaises(ValueError):
            validate_release_deploy_gate(gate, self.post_merge(), CONFIG)

    def test_unhealthy_post_merge_is_rejected(self):
        post = self.post_merge()
        post.loc[0, "post_merge_state"] = "needs_investigation"
        with self.assertRaises(ValueError):
            validate_release_deploy_gate(self.gate(), post, CONFIG)

    def test_eligible_deploy_requires_monitoring_ready(self):
        gate = self.gate()
        gate.loc[0, "monitoring_readiness_status"] = "failed"
        with self.assertRaises(ValueError):
            validate_release_deploy_gate(gate, self.post_merge(), CONFIG)

    def test_blocked_can_record_failed_gate(self):
        gate = self.gate("blocked")
        gate.loc[0, "predeploy_ci_status"] = "failed"
        out = validate_release_deploy_gate(
            gate,
            self.post_merge(),
            CONFIG,
        )
        self.assertEqual(out.iloc[0]["final_release_decision"], "blocked")


if __name__ == "__main__":
    unittest.main()
