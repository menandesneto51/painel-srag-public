# -*- coding: utf-8 -*-
import unittest

import pandas as pd

from src.rule_shadow_evaluation_v2_7 import (
    compare_shadow_assignments,
    summarize_shadow_evaluation,
)


def assignments(queue_a: str, queue_b: str | None = None):
    rows = []
    for i in range(142):
        code = f"51{i:05d}"
        queue = queue_a
        if queue_b is not None and i == 0:
            queue = queue_b
        rows.append({
            "codigo_ibge": code,
            "municipio": f"Municipio {i}",
            "review_queue": queue,
        })
    return pd.DataFrame(rows)


class RuleShadowEvaluationV27Tests(unittest.TestCase):
    def test_shadow_detects_queue_change_without_activation(self):
        current = assignments("routine_monitoring")
        candidate = assignments(
            "routine_monitoring",
            "epidemiology_review",
        )
        shadow = compare_shadow_assignments(
            current,
            candidate,
            required_municipalities=142,
            proposal_id="prop_1",
            candidate_rule_version="candidate-1",
        )
        summary = summarize_shadow_evaluation(shadow)
        self.assertEqual(summary["municipalities_with_queue_change"], 1)
        self.assertTrue(summary["shadow_only"])
        self.assertFalse(summary["automatic_activation"])
        self.assertFalse(summary["reviewer_scoring"])

    def test_candidate_can_improve_workflow_agreement_without_being_gold_standard(self):
        current = assignments("epidemiology_review")
        candidate = assignments("routine_monitoring")
        decisions = pd.DataFrame([{
            "decision_record_id": "d1",
            "codigo_ibge": "5100000",
            "decision_status": "continue_monitoring",
        }])
        shadow = compare_shadow_assignments(
            current,
            candidate,
            required_municipalities=142,
            decisions=decisions,
            routine_queue="routine_monitoring",
            escalation_decisions={"request_epi_investigation"},
            non_escalation_decisions={"continue_monitoring"},
        )
        row = shadow.loc[shadow["decision_record_id"].eq("d1")].iloc[0]
        self.assertEqual(
            row["alignment_delta"],
            "workflow_agreement_improved",
        )
        self.assertFalse(
            bool(row["human_decision_is_epidemiological_gold_standard"])
        )

    def test_missing_municipality_is_rejected(self):
        current = assignments("routine_monitoring")
        candidate = assignments("routine_monitoring").iloc[:-1].copy()
        with self.assertRaises(ValueError):
            compare_shadow_assignments(
                current,
                candidate,
                required_municipalities=142,
            )


if __name__ == "__main__":
    unittest.main()
