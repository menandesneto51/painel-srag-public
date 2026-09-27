# -*- coding: utf-8 -*-
import unittest

import pandas as pd

from src.rule_shadow_evaluation_report_v2_7 import (
    build_shadow_metadata,
    render_shadow_report,
)


class RuleShadowEvaluationReportV27Tests(unittest.TestCase):
    def frame(self):
        return pd.DataFrame([
            {
                "codigo_ibge": "5103403",
                "municipio": "Cuiabá",
                "current_review_queue": "epidemiology_review",
                "candidate_review_queue": "routine_monitoring",
                "queue_changed": True,
                "queue_transition": "epidemiology_review -> routine_monitoring",
                "decision_record_id": "d1",
                "decision_status": "continue_monitoring",
                "current_alignment": "nonroutine_not_escalated_rule_review",
                "candidate_alignment": "routine_non_escalation_aligned",
                "alignment_delta": "workflow_agreement_improved",
                "proposal_id": "prop_1",
                "candidate_rule_version": "candidate-1",
                "shadow_only": True,
                "automatic_activation_enabled": False,
                "automatic_rule_change_enabled": False,
                "reviewer_score_enabled": False,
                "municipality_rank_enabled": False,
                "human_decision_is_epidemiological_gold_standard": False,
            }
        ])

    def test_metadata_keeps_shadow_governance(self):
        metadata = build_shadow_metadata(
            self.frame(),
            proposal_id="prop_1",
            proposal_status="needs_backtest",
            current_rule_version="current",
            candidate_rule_version="candidate-1",
        )
        self.assertTrue(metadata["shadow_only"])
        self.assertFalse(metadata["candidate_rule_activated"])
        self.assertFalse(metadata["reviewer_scoring"])
        self.assertFalse(metadata["municipality_ranking"])
        self.assertTrue(
            metadata["workflow_agreement_is_not_epidemiological_accuracy"]
        )

    def test_report_states_no_activation(self):
        report = render_shadow_report(
            self.frame(),
            proposal_id="prop_1",
            proposal_status="needs_backtest",
            current_rule_version="current",
            candidate_rule_version="candidate-1",
        )
        self.assertIn("regra candidata não foi ativada", report)
        self.assertIn(
            "não significa maior acurácia epidemiológica",
            report,
        )


if __name__ == "__main__":
    unittest.main()
