# -*- coding: utf-8 -*-
import unittest

import pandas as pd

from src.human_review_decisions import validate_review_decisions


class HumanReviewDecisionTests(unittest.TestCase):
    def valid(self):
        return pd.DataFrame([{
            "codigo_ibge": "5103403",
            "municipio": "Cuiabá",
            "review_queue": "epidemiology_review",
            "reviewed_at": "2026-09-27T08:00:00-04:00",
            "reviewer_role": "epidemiologista",
            "decision_status": "continue_monitoring",
            "rationale": "Sinal revisado; manter acompanhamento na próxima atualização.",
            "evidence_refs": "combined_signals;virology",
        }])

    def test_human_decision_is_audit_record_only(self):
        out = validate_review_decisions(self.valid())
        row = out.iloc[0]
        self.assertTrue(bool(row["decision_recorded_by_human"]))
        self.assertFalse(bool(row["automatic_execution_enabled"]))
        self.assertFalse(bool(row["patient_level_decision_enabled"]))

    def test_unknown_decision_is_rejected(self):
        frame = self.valid()
        frame.loc[0, "decision_status"] = "automatic_alert"
        with self.assertRaises(ValueError):
            validate_review_decisions(frame)

    def test_empty_rationale_is_rejected(self):
        frame = self.valid()
        frame.loc[0, "rationale"] = ""
        with self.assertRaises(ValueError):
            validate_review_decisions(frame)


if __name__ == "__main__":
    unittest.main()
