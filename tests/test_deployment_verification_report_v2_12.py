# -*- coding: utf-8 -*-
import unittest

import pandas as pd

from src.deployment_verification_report_v2_12 import (
    build_deployment_verification_summary,
    render_deployment_verification_markdown,
)


class DeploymentVerificationReportV212Tests(unittest.TestCase):
    def test_summary_keeps_execution_layers_separate(self):
        decisions = pd.DataFrame([{
            "deploy_decision_record_id": "d1",
            "deploy_decision": "approve_human_deploy",
            "deploy_decision_is_not_deploy_execution": True,
            "automatic_deploy_enabled": False,
            "automatic_rollback_enabled": False,
        }])
        deployments = pd.DataFrame([{
            "deployment_record_id": "x1",
            "deployment_state": "verified_healthy",
            "deployment_record_requires_actual_deploy_evidence": True,
            "deployment_is_not_effect_verification": True,
            "automatic_deploy_enabled": False,
            "automatic_rollback_enabled": False,
        }])
        effects = pd.DataFrame([{
            "effect_verification_record_id": "e1",
            "effect_state": "implementation_behavior_verified",
            "effect_verification_is_not_causal_inference": True,
            "automatic_rule_change_enabled": False,
            "automatic_rollback_enabled": False,
        }])

        summary = build_deployment_verification_summary(
            decisions, deployments, effects
        )
        self.assertEqual(summary["deploy_decision_records"], 1)
        self.assertEqual(summary["deployment_records"], 1)
        self.assertEqual(summary["effect_verification_records"], 1)
        self.assertFalse(summary["automatic_deploy_enabled"])
        self.assertTrue(
            summary["effect_verification_is_not_causal_inference"]
        )

    def test_report_rejects_causal_interpretation(self):
        summary = build_deployment_verification_summary(None, None, None)
        report = render_deployment_verification_markdown(summary)
        self.assertIn("não é inferência causal epidemiológica", report)
        self.assertIn("Rollback automático", report)


if __name__ == "__main__":
    unittest.main()
