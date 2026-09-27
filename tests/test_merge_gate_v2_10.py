# -*- coding: utf-8 -*-
import unittest

import pandas as pd

from src.merge_gate_v2_10 import validate_merge_gate


CONFIG = {
    "allowed_package_status": ["ready_for_manual_branch"],
    "review_statuses": ["passed", "failed", "not_applicable"],
    "final_gate_decisions": [
        "eligible_for_human_merge",
        "blocked",
        "defer",
    ],
    "protected_branch_names": ["main", "master"],
    "logic_change_types": [
        "queue_rule",
        "action_trigger",
        "threshold",
        "context_requirement",
    ],
    "documentation_only_types": ["documentation"],
}


class MergeGateV210Tests(unittest.TestCase):
    def package(self, proposal_type="queue_rule"):
        return pd.DataFrame([{
            "implementation_package_id": "implpkg_1",
            "proposal_id": "prop_1",
            "evaluation_record_id": "eval_1",
            "proposal_type": proposal_type,
            "package_status": "ready_for_manual_branch",
            "source_branch": "v2-saneamento-epidemiologico",
            "source_commit_sha": "1" * 40,
            "target_paths": (
                "config/operational_review_v2_2.json | "
                "tests/test_operational_review.py"
            ),
            "package_is_not_implementation": True,
            "manual_branch_required": True,
            "automatic_branch_creation_enabled": False,
            "automatic_code_edit_enabled": False,
            "automatic_commit_enabled": False,
            "automatic_merge_enabled": False,
            "automatic_deploy_enabled": False,
            "human_review_required": True,
        }])

    def gate(self, decision="eligible_for_human_merge"):
        return pd.DataFrame([{
            "implementation_package_id": "implpkg_1",
            "evaluated_at": "2026-09-27T13:00:00Z",
            "reviewer_role": "revisor_tecnico",
            "implementation_branch": "change/prop_1",
            "source_commit_sha": "1" * 40,
            "implementation_commit_sha": "2" * 40,
            "changed_paths": (
                "config/operational_review_v2_2.json | "
                "tests/test_operational_review.py"
            ),
            "diff_review_status": "passed",
            "scope_review_status": "passed",
            "ci_status": "passed",
            "regression_tests_status": "passed",
            "backtest_status": "passed",
            "epidemiology_revalidation_status": "passed",
            "statistical_revalidation_status": "passed",
            "security_privacy_review_status": "passed",
            "acceptance_criteria_status": "passed",
            "rollback_verification_status": "passed",
            "final_gate_decision": decision,
            "gate_rationale": "Todos os gates obrigatórios foram aprovados.",
        }])

    def test_eligible_record_is_not_merge(self):
        out = validate_merge_gate(
            self.gate(),
            self.package(),
            CONFIG,
        )
        row = out.iloc[0]
        self.assertEqual(
            row["final_gate_decision"],
            "eligible_for_human_merge",
        )
        self.assertTrue(bool(row["merge_eligibility_is_not_merge"]))
        self.assertTrue(bool(row["human_merge_required"]))
        self.assertFalse(bool(row["automatic_merge_enabled"]))
        self.assertFalse(bool(row["automatic_deploy_enabled"]))

    def test_protected_branch_is_rejected(self):
        gate = self.gate()
        gate.loc[0, "implementation_branch"] = "main"
        with self.assertRaises(ValueError):
            validate_merge_gate(
                gate,
                self.package(),
                CONFIG,
            )

    def test_source_commit_must_match_package(self):
        gate = self.gate()
        gate.loc[0, "source_commit_sha"] = "3" * 40
        with self.assertRaises(ValueError):
            validate_merge_gate(
                gate,
                self.package(),
                CONFIG,
            )

    def test_implementation_commit_must_differ(self):
        gate = self.gate()
        gate.loc[0, "implementation_commit_sha"] = "1" * 40
        with self.assertRaises(ValueError):
            validate_merge_gate(
                gate,
                self.package(),
                CONFIG,
            )

    def test_unauthorized_diff_path_is_rejected(self):
        gate = self.gate()
        gate.loc[0, "changed_paths"] = "src/unplanned_file.py"
        with self.assertRaises(ValueError):
            validate_merge_gate(
                gate,
                self.package(),
                CONFIG,
            )

    def test_eligible_merge_requires_passed_backtest_for_logic(self):
        gate = self.gate()
        gate.loc[0, "backtest_status"] = "failed"
        with self.assertRaises(ValueError):
            validate_merge_gate(
                gate,
                self.package(),
                CONFIG,
            )

    def test_documentation_change_allows_not_applicable_backtest(self):
        gate = self.gate()
        gate.loc[0, "backtest_status"] = "not_applicable"
        gate.loc[0, "statistical_revalidation_status"] = "not_applicable"
        out = validate_merge_gate(
            gate,
            self.package("documentation"),
            CONFIG,
        )
        self.assertEqual(
            out.iloc[0]["final_gate_decision"],
            "eligible_for_human_merge",
        )

    def test_blocked_decision_can_record_failed_gate(self):
        gate = self.gate("blocked")
        gate.loc[0, "ci_status"] = "failed"
        out = validate_merge_gate(
            gate,
            self.package(),
            CONFIG,
        )
        self.assertEqual(out.iloc[0]["final_gate_decision"], "blocked")


if __name__ == "__main__":
    unittest.main()
