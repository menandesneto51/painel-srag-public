# -*- coding: utf-8 -*-
import unittest

import pandas as pd

from src.operational_actions import (
    build_operational_action_suggestions,
    summarize_action_suggestions,
)


MATRIX = {
    "sources": {
        "s": {"title": "Fonte", "url": "https://example.org"}
    },
    "actions": [
        {
            "action_id": "SURV-01",
            "domain": "surveillance",
            "title": "Revisar sinal",
            "trigger_tags_any": ["epidemiology_review"],
            "suggested_review_owner": "vigilancia",
            "suggested_timeframe": "revisao_atual",
            "action_text": "Revisar sinal.",
            "source_refs": ["s"],
        },
        {
            "action_id": "COM-01",
            "domain": "risk_communication",
            "title": "Avaliar comunicação",
            "trigger_signal_status_any": ["elevated_and_rising_experimental"],
            "requires_signal_confidence_any": ["high_experimental"],
            "suggested_review_owner": "cievs",
            "suggested_timeframe": "apos_validacao",
            "action_text": "Avaliar comunicação.",
            "source_refs": ["s"],
        },
        {
            "action_id": "RAS-01",
            "domain": "healthcare_network",
            "title": "Revisar rede",
            "trigger_tags_any": ["healthcare_coordination"],
            "requires_healthcare_pressure_available": True,
            "requires_pressure_validation_status": ["validated"],
            "suggested_review_owner": "regulacao",
            "suggested_timeframe": "coordenacao",
            "action_text": "Revisar rede.",
            "source_refs": ["s"],
        },
    ],
}


class OperationalActionTests(unittest.TestCase):
    def territorial(self):
        return pd.DataFrame([{
            "codigo_ibge": "5103403",
            "municipio": "Cuiabá",
            "signal_status": "elevated_and_rising_experimental",
            "signal_confidence": "high_experimental",
            "silence_status": "activity_present",
            "virology_status": "named_agent_detected",
            "virology_dominant_agent": "Influenza A",
            "healthcare_pressure_available": False,
            "pressure_status": pd.NA,
            "validation_status": "not_available",
            "territorial_model_status": "under_calibration",
        }])

    def cards(self):
        return pd.DataFrame([{
            "codigo_ibge": "5103403",
            "review_tags": "epidemiology_review|virology_review",
            "evidence_summary": "atividade acima do esperado.",
            "review_notes": "",
        }])

    def test_actions_are_suggestions_not_execution(self):
        out = build_operational_action_suggestions(
            self.territorial(), self.cards(), MATRIX
        )
        ids = set(out["action_id"])
        self.assertIn("SURV-01", ids)
        self.assertIn("COM-01", ids)
        self.assertNotIn("RAS-01", ids)
        self.assertTrue(out["human_review_required"].all())
        self.assertFalse(out["automatic_execution"].any())
        self.assertFalse(out["clinical_prescription"].any())
        self.assertFalse(out["composite_score_used"].any())

    def test_healthcare_action_requires_validated_pressure(self):
        territorial = self.territorial()
        territorial.loc[0, "healthcare_pressure_available"] = True
        territorial.loc[0, "pressure_status"] = "high"
        territorial.loc[0, "validation_status"] = "validated"
        cards = self.cards()
        cards.loc[0, "review_tags"] += "|healthcare_coordination"
        out = build_operational_action_suggestions(
            territorial, cards, MATRIX
        )
        self.assertIn("RAS-01", set(out["action_id"]))

    def test_summary_counts_municipalities(self):
        out = build_operational_action_suggestions(
            self.territorial(), self.cards(), MATRIX
        )
        summary = summarize_action_suggestions(out)
        self.assertTrue((summary["municipalities"] == 1).all())


if __name__ == "__main__":
    unittest.main()
