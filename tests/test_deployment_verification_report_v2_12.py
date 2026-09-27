# -*- coding: utf-8 -*-
import unittest

import pandas as pd

from src.deployment_verification_report_v2_12 import (
    build_deployment_verification_summary,
    render_deployment_verification_markdown,
)


class DeploymentVerificationReportV212Tests(unittest.TestCase):
    def release_gate(self):
        return pd.DataFrame([{
            "release_gate_record_id": "rg1",
            "final_release_decision": "eligible_for_human_deploy",
            "deploy_eligibility_is_not_deploy": True,
            "automatic_deploy_enabled": False,
            "automatic_rollback_enabled": False,
            "human_deploy_required": True,
        }])

    def decisions(self):
        return pd.DataFrame([{
            "deploy_decision_record_id": "d1",
            "release_gate_record_id": "rg1",
            "deploy_decision": "approve_human_deploy",
            "release_gate_required": True,
            "deploy_decision_is_not_deploy_execution": True,
            "automatic_deploy_enabled": False,
            "automatic_rollback_enabled": False,
        }])

    def deployments(self):
        return pd.DataFrame([{
            "deployment_record_id": "x1",
            "release_gate_record_id": "rg1",
            "deployment_state": "verified_healthy",
            "deployment_record_requires_actual_deploy_evidence": True,
            "release_gate_required": True,
            "deployment_is_not_effect_verification": True,
            "automatic_deploy_enabled": False,
            "automatic_rollback_enabled": False,
        }])

    def effects(self):
        return pd.DataFrame([{
            "effect_verification_record_id": "e1",
            "effect_state": "implementation_behavior_verified",
            "effect_verification_is_not_causal_inference": True,
            "automatic_rule_change_enabled": False,
            "automatic_rollback_enabled": False,
        }])

    def test_summary_keeps_execution_layers_separate(self):
        summary = build_deployment_verification_summary(
            self.release_gate(),
            self.decisions(),
            self.deployments(),
            self.effects(),
        )
        self.assertEqual(summary["release_gate_records"], 1)
        self.assertEqual(summary["eligible_release_gate_records"], 1)
        self.assertEqual(summary["deploy_decision_records"], 1)
        self.assertEqual(summary["deployment_records"], 1)
        self.assertEqual(summary["effect_verification_records"], 1)
        self.assertTrue(summary["release_gate_required"])
        self.assertFalse(summary["automatic_deploy_enabled"])
        self.assertTrue(
            summary["effect_verification_is_not_causal_inference"]
        )

    def test_report_rejects_causal_interpretation(self):
        summary = build_deployment_verification_summary(
            None, None, None, None
        )
        report = render_deployment_verification_markdown(summary)
        self.assertIn("Gate de release não é deploy", report)
        self.assertIn("não é inferência causal epidemiológica", report)
        self.assertIn("Rollback automático", report)


if __name__ == "__main__":
    unittest.main()
