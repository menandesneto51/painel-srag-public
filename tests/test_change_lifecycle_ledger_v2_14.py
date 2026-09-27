# -*- coding: utf-8 -*-
import unittest

import pandas as pd

from src.change_lifecycle_ledger_v2_14 import (
    build_change_lifecycle_ledger,
    summarize_change_lifecycle_ledger,
)


CONFIG = {
    "stage_order": {
        "proposal": 10,
        "evaluation": 20,
        "implementation_package": 30,
        "merge_gate": 40,
        "merge_decision": 50,
        "post_merge": 60,
        "release_gate": 70,
        "deploy_decision": 80,
        "deployment": 90,
        "effect_verification": 100,
        "rollback_decision": 110,
        "rollback_execution": 120,
    },
    "allowed_transitions": {
        "proposal": ["evaluation"],
        "evaluation": ["implementation_package"],
        "implementation_package": ["merge_gate"],
        "merge_gate": ["merge_decision"],
        "merge_decision": ["post_merge"],
        "post_merge": ["release_gate"],
        "release_gate": ["deploy_decision"],
        "deploy_decision": ["deployment"],
        "deployment": ["effect_verification", "rollback_decision"],
        "effect_verification": ["rollback_decision"],
        "rollback_decision": ["rollback_execution"],
        "rollback_execution": [],
    },
    "commit_continuity_children": [
        "merge_decision",
        "release_gate",
        "deploy_decision",
        "deployment",
        "effect_verification",
        "rollback_execution",
    ],
}


class ChangeLifecycleLedgerV214Tests(unittest.TestCase):
    def frames(self):
        proposals = pd.DataFrame([{
            "proposal_id": "prop_1",
            "proposal_status": "ready_for_human_decision",
        }])
        evaluations = pd.DataFrame([{
            "evaluation_record_id": "eval_1",
            "proposal_id": "prop_1",
            "evaluated_at": "2026-09-27T10:00:00Z",
            "final_decision": "approve_for_implementation_branch",
        }])
        packages = pd.DataFrame([{
            "implementation_package_id": "implpkg_1",
            "proposal_id": "prop_1",
            "evaluation_record_id": "eval_1",
            "created_at": "2026-09-27T11:00:00Z",
            "package_status": "ready_for_manual_branch",
            "source_commit_sha": "1" * 40,
        }])
        merge_gates = pd.DataFrame([{
            "merge_gate_record_id": "mg_1",
            "implementation_package_id": "implpkg_1",
            "proposal_id": "prop_1",
            "evaluated_at": "2026-09-27T12:00:00Z",
            "final_gate_decision": "eligible_for_human_merge",
            "implementation_commit_sha": "2" * 40,
        }])
        merge_decisions = pd.DataFrame([{
            "merge_decision_record_id": "md_1",
            "merge_gate_record_id": "mg_1",
            "implementation_package_id": "implpkg_1",
            "proposal_id": "prop_1",
            "decided_at": "2026-09-27T12:30:00Z",
            "merge_decision": "approve_human_merge",
            "implementation_commit_sha": "2" * 40,
        }])
        post_merge = pd.DataFrame([{
            "post_merge_record_id": "pm_1",
            "merge_decision_record_id": "md_1",
            "implementation_package_id": "implpkg_1",
            "recorded_at": "2026-09-27T13:00:00Z",
            "post_merge_state": "verified_healthy",
            "merged_commit_sha": "3" * 40,
        }])
        release_gates = pd.DataFrame([{
            "release_gate_record_id": "rg_1",
            "post_merge_record_id": "pm_1",
            "implementation_package_id": "implpkg_1",
            "evaluated_at": "2026-09-27T13:30:00Z",
            "final_release_decision": "eligible_for_human_deploy",
            "release_commit_sha": "3" * 40,
            "target_environment": "prd",
        }])
        deploy_decisions = pd.DataFrame([{
            "deploy_decision_record_id": "dd_1",
            "release_gate_record_id": "rg_1",
            "implementation_package_id": "implpkg_1",
            "decided_at": "2026-09-27T14:00:00Z",
            "deploy_decision": "approve_human_deploy",
            "release_commit_sha": "3" * 40,
            "target_environment": "prd",
        }])
        deployments = pd.DataFrame([{
            "deployment_record_id": "dep_1",
            "deploy_decision_record_id": "dd_1",
            "implementation_package_id": "implpkg_1",
            "deployed_at": "2026-09-27T14:30:00Z",
            "deployment_state": "verified_healthy",
            "deployed_commit_sha": "3" * 40,
            "environment": "prd",
        }])
        effects = pd.DataFrame([{
            "effect_verification_record_id": "eff_1",
            "deployment_record_id": "dep_1",
            "implementation_package_id": "implpkg_1",
            "measured_at": "2026-10-05T12:00:00Z",
            "effect_state": "implementation_behavior_verified",
            "deployed_commit_sha": "3" * 40,
        }])
        return {
            "proposals": proposals,
            "evaluations": evaluations,
            "packages": packages,
            "merge_gates": merge_gates,
            "merge_decisions": merge_decisions,
            "post_merge": post_merge,
            "release_gates": release_gates,
            "deploy_decisions": deploy_decisions,
            "deployments": deployments,
            "effects": effects,
        }

    def build(self, **overrides):
        frames = self.frames()
        frames.update(overrides)
        return build_change_lifecycle_ledger(
            **frames,
            rollback_decisions=None,
            rollback_executions=None,
            config=CONFIG,
        )

    def test_builds_linked_end_to_end_ledger(self):
        ledger = self.build()
        self.assertEqual(len(ledger), 10)
        self.assertTrue(
            (ledger["lineage_status"] == "linked_and_validated").all()
        )
        self.assertTrue(ledger["ledger_is_not_execution"].all())
        self.assertFalse(ledger["automatic_action_enabled"].any())

        summary = summarize_change_lifecycle_ledger(ledger)
        self.assertEqual(summary["proposals"], 1)
        self.assertEqual(summary["orphan_events"], 0)
        self.assertFalse(summary["automatic_action_enabled"])

    def test_orphan_parent_is_rejected(self):
        frames = self.frames()
        frames["deploy_decisions"].loc[
            0, "release_gate_record_id"
        ] = "missing"
        with self.assertRaises(ValueError):
            self.build(
                deploy_decisions=frames["deploy_decisions"]
            )

    def test_commit_break_is_rejected(self):
        frames = self.frames()
        frames["deployments"].loc[0, "deployed_commit_sha"] = "4" * 40
        with self.assertRaises(ValueError):
            self.build(deployments=frames["deployments"])

    def test_environment_break_is_rejected(self):
        frames = self.frames()
        frames["deployments"].loc[0, "environment"] = "hml"
        with self.assertRaises(ValueError):
            self.build(deployments=frames["deployments"])

    def test_backward_chronology_is_rejected(self):
        frames = self.frames()
        frames["release_gates"].loc[
            0, "evaluated_at"
        ] = "2026-09-27T12:00:00Z"
        with self.assertRaises(ValueError):
            self.build(release_gates=frames["release_gates"])

    def test_rollback_branch_is_supported(self):
        frames = self.frames()
        rollback_decisions = pd.DataFrame([{
            "rollback_decision_record_id": "rbd_1",
            "source_record_type": "effect",
            "source_record_id": "eff_1",
            "implementation_package_id": "implpkg_1",
            "decided_at": "2026-10-05T13:00:00Z",
            "rollback_decision": "approve_human_rollback",
            "rollback_target_commit_sha": "1" * 40,
        }])
        rollback_executions = pd.DataFrame([{
            "rollback_execution_record_id": "rbx_1",
            "rollback_decision_record_id": "rbd_1",
            "implementation_package_id": "implpkg_1",
            "rolled_back_at": "2026-10-05T14:00:00Z",
            "rollback_execution_state": "verified_restored",
            "rolled_back_commit_sha": "1" * 40,
        }])

        ledger = build_change_lifecycle_ledger(
            **frames,
            rollback_decisions=rollback_decisions,
            rollback_executions=rollback_executions,
            config=CONFIG,
        )
        self.assertIn(
            "rollback_execution:rbx_1",
            set(ledger["event_key"]),
        )


if __name__ == "__main__":
    unittest.main()
