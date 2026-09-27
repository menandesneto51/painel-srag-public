# -*- coding: utf-8 -*-
import unittest

import pandas as pd

from src.human_merge_record_v2_11 import (
    validate_human_merge_decisions,
    validate_post_merge_records,
)


CONFIG = {
    "allowed_gate_decision": "eligible_for_human_merge",
    "merge_decisions": [
        "approve_human_merge",
        "reject_merge",
        "defer_merge",
    ],
    "post_merge_states": [
        "verified_healthy",
        "needs_investigation",
        "rollback_consideration",
    ],
    "verification_statuses": ["passed", "failed", "not_applicable"],
    "rollback_readiness_statuses": ["ready", "blocked", "not_applicable"],
}


class HumanMergeRecordV211Tests(unittest.TestCase):
    def gate(self):
        return pd.DataFrame([{
            "merge_gate_record_id": "mergegate_1",
            "implementation_package_id": "implpkg_1",
            "proposal_id": "prop_1",
            "evaluation_record_id": "eval_1",
            "implementation_branch": "change/prop_1",
            "implementation_commit_sha": "2" * 40,
            "final_gate_decision": "eligible_for_human_merge",
            "merge_eligibility_is_not_merge": True,
            "automatic_merge_enabled": False,
            "automatic_deploy_enabled": False,
            "human_merge_required": True,
        }])

    def decision(self, merge_decision="approve_human_merge"):
        return pd.DataFrame([{
            "merge_gate_record_id": "mergegate_1",
            "decided_at": "2026-09-27T14:00:00Z",
            "reviewer_role": "revisor_merge",
            "merge_decision": merge_decision,
            "decision_rationale": "Revisão humana concluída.",
        }])

    def post_merge(self):
        return pd.DataFrame([{
            "merge_decision_record_id": "placeholder",
            "recorded_at": "2026-09-27T14:30:00Z",
            "reviewer_role": "revisor_pos_merge",
            "merged_commit_sha": "3" * 40,
            "merge_evidence_ref": "pr#123-merge-event",
            "post_merge_ci_status": "passed",
            "smoke_test_status": "passed",
            "epidemiology_sanity_status": "passed",
            "security_privacy_check_status": "passed",
            "rollback_readiness_status": "ready",
            "post_merge_state": "verified_healthy",
            "verification_notes": "Verificação pós-merge concluída.",
        }])

    def test_merge_decision_does_not_execute_merge(self):
        out = validate_human_merge_decisions(
            self.decision(),
            self.gate(),
            CONFIG,
        )
        row = out.iloc[0]
        self.assertTrue(bool(row["merge_decision_is_not_merge_execution"]))
        self.assertFalse(bool(row["automatic_merge_enabled"]))
        self.assertFalse(bool(row["automatic_deploy_enabled"]))
        self.assertFalse(bool(row["automatic_rollback_enabled"]))

    def test_noneligible_gate_cannot_be_decided_for_merge(self):
        gate = self.gate()
        gate.loc[0, "final_gate_decision"] = "blocked"
        with self.assertRaises(ValueError):
            validate_human_merge_decisions(
                self.decision(),
                gate,
                CONFIG,
            )

    def test_post_merge_requires_approved_human_merge(self):
        decisions = validate_human_merge_decisions(
            self.decision("reject_merge"),
            self.gate(),
            CONFIG,
        )
        record = self.post_merge()
        record.loc[0, "merge_decision_record_id"] = decisions.iloc[0][
            "merge_decision_record_id"
        ]
        with self.assertRaises(ValueError):
            validate_post_merge_records(record, decisions, CONFIG)

    def test_post_merge_requires_merge_evidence(self):
        decisions = validate_human_merge_decisions(
            self.decision(),
            self.gate(),
            CONFIG,
        )
        record = self.post_merge()
        record.loc[0, "merge_decision_record_id"] = decisions.iloc[0][
            "merge_decision_record_id"
        ]
        record.loc[0, "merge_evidence_ref"] = ""
        with self.assertRaises(ValueError):
            validate_post_merge_records(record, decisions, CONFIG)

    def test_verified_healthy_requires_all_checks_and_rollback_ready(self):
        decisions = validate_human_merge_decisions(
            self.decision(),
            self.gate(),
            CONFIG,
        )
        record = self.post_merge()
        record.loc[0, "merge_decision_record_id"] = decisions.iloc[0][
            "merge_decision_record_id"
        ]
        out = validate_post_merge_records(record, decisions, CONFIG)
        row = out.iloc[0]
        self.assertEqual(row["post_merge_state"], "verified_healthy")
        self.assertTrue(
            bool(row["post_merge_record_requires_actual_merge_evidence"])
        )
        self.assertFalse(bool(row["automatic_deploy_enabled"]))
        self.assertFalse(bool(row["automatic_rollback_enabled"]))

    def test_verified_healthy_rejects_failed_smoke_test(self):
        decisions = validate_human_merge_decisions(
            self.decision(),
            self.gate(),
            CONFIG,
        )
        record = self.post_merge()
        record.loc[0, "merge_decision_record_id"] = decisions.iloc[0][
            "merge_decision_record_id"
        ]
        record.loc[0, "smoke_test_status"] = "failed"
        with self.assertRaises(ValueError):
            validate_post_merge_records(record, decisions, CONFIG)


if __name__ == "__main__":
    unittest.main()
