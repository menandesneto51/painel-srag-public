# -*- coding: utf-8 -*-
import unittest

import pandas as pd

from src.implementation_package_v2_9 import validate_implementation_packages


CONFIG = {
    "allowed_source_decision": "approve_for_implementation_branch",
    "allowed_source_evaluation_status": ["human_rule_change_evaluation"],
    "allowed_source_proposal_status": ["ready_for_human_decision"],
    "logic_change_types": ["queue_rule", "action_trigger", "threshold", "context_requirement"],
    "documentation_only_types": ["documentation"],
    "package_statuses": ["draft", "ready_for_manual_branch", "blocked", "superseded"],
    "protected_path_prefixes": [
        "data_raw/",
        "data_internal/",
        "data_candidate/",
        "data_public/",
        ".git/",
        "secrets/",
        "credentials/",
    ],
    "protected_exact_paths": [".env"],
}


class ImplementationPackageV29Tests(unittest.TestCase):
    def evaluations(self, decision="approve_for_implementation_branch"):
        return pd.DataFrame([{
            "evaluation_record_id": "eval_1",
            "proposal_id": "prop_1",
            "proposal_type": "queue_rule",
            "source_proposal_status": "ready_for_human_decision",
            "final_decision": decision,
            "case_review_status": "passed",
            "epidemiology_review_status": "passed",
            "shadow_review_status": "passed",
            "shadow_evidence_present": True,
            "shadow_candidate_rule_version": "candidate-v1",
            "shadow_review_is_not_activation": True,
            "backtest_status": "passed",
            "statistical_review_status": "passed",
            "documentation_status": "passed",
            "evaluation_recorded_by_human": True,
            "proposal_is_not_change": True,
            "decision_is_not_implementation": True,
            "automatic_rule_change_enabled": False,
            "automatic_threshold_change_enabled": False,
            "automatic_merge_enabled": False,
            "automatic_deploy_enabled": False,
            "human_approval_required": True,
            "personal_identifier_storage": False,
            "evaluation_status": "human_rule_change_evaluation",
        }])

    def proposals(self):
        return pd.DataFrame([{
            "proposal_id": "prop_1",
            "proposal_type": "queue_rule",
            "proposal_status": "ready_for_human_decision",
            "rule_key": "review_queue::epidemiology_review",
            "proposal_is_not_change": True,
            "human_approval_required": True,
            "automatic_rule_change_enabled": False,
            "automatic_threshold_change_enabled": False,
        }])

    def package(self):
        return pd.DataFrame([{
            "proposal_id": "prop_1",
            "evaluation_record_id": "eval_1",
            "created_at": "2026-09-27T11:00:00Z",
            "planner_role": "engenharia_analitica",
            "source_branch": "v2-saneamento-epidemiologico",
            "source_commit_sha": "0123456789abcdef0123456789abcdef01234567",
            "implementation_summary": "Ajustar regra candidata em branch separada.",
            "target_paths": "config/operational_review_v2_2.json | tests/test_operational_review.py",
            "required_tests": "unit|regression|backtest",
            "acceptance_criteria": "CI verde e comportamento esperado no modo sombra.",
            "rollback_plan": "Reverter commit da branch de mudança.",
            "evidence_refs": "prop_1|eval_1",
            "package_status": "ready_for_manual_branch",
        }])

    def test_approved_evaluation_generates_non_automatic_package(self):
        out = validate_implementation_packages(
            self.package(),
            self.evaluations(),
            self.proposals(),
            CONFIG,
        )
        row = out.iloc[0]
        self.assertTrue(bool(row["package_is_not_implementation"]))
        self.assertTrue(bool(row["manual_branch_required"]))
        self.assertFalse(bool(row["automatic_branch_creation_enabled"]))
        self.assertFalse(bool(row["automatic_code_edit_enabled"]))
        self.assertFalse(bool(row["automatic_commit_enabled"]))
        self.assertFalse(bool(row["automatic_merge_enabled"]))
        self.assertFalse(bool(row["automatic_deploy_enabled"]))

    def test_nonapproved_evaluation_is_rejected(self):
        with self.assertRaises(ValueError):
            validate_implementation_packages(
                self.package(),
                self.evaluations("defer"),
                self.proposals(),
                CONFIG,
            )

    def test_protected_path_is_rejected(self):
        package = self.package()
        package.loc[0, "target_paths"] = ".env"
        with self.assertRaises(ValueError):
            validate_implementation_packages(
                package,
                self.evaluations(),
                self.proposals(),
                CONFIG,
            )

    def test_parent_traversal_is_rejected(self):
        package = self.package()
        package.loc[0, "target_paths"] = "../outside.json"
        with self.assertRaises(ValueError):
            validate_implementation_packages(
                package,
                self.evaluations(),
                self.proposals(),
                CONFIG,
            )


if __name__ == "__main__":
    unittest.main()
