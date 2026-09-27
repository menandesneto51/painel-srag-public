# -*- coding: utf-8 -*-
import unittest

import pandas as pd

from src.operational_review import build_operational_review_queue
from src.state_review_report import build_state_review_summary


def config():
    return {
        "review_tag_actions": {
            "epidemiology_review": ["Revisar epidemiologia."],
            "data_quality_review": ["Revisar qualidade."],
            "virology_review": ["Revisar virologia."],
            "healthcare_coordination": ["Revisar assistência."],
        },
        "queue_rules": [
            {
                "queue": "data_validation_first",
                "requires_any_tags": ["data_quality_review"],
                "description": "Dados primeiro",
            },
            {
                "queue": "multidisciplinary_review",
                "requires_all_tags": ["epidemiology_review", "healthcare_coordination"],
                "description": "Revisão conjunta",
            },
            {
                "queue": "epidemiology_virology_review",
                "requires_all_tags": ["epidemiology_review", "virology_review"],
                "description": "Epi + virologia",
            },
            {
                "queue": "epidemiology_review",
                "requires_any_tags": ["epidemiology_review"],
                "description": "Epidemiologia",
            },
            {"queue": "routine_monitoring", "description": "Rotina"},
        ],
    }


class OperationalReviewTests(unittest.TestCase):
    def base_card(self, tags: str):
        return {
            "codigo_ibge": "5103403",
            "municipio": "Cuiabá",
            "review_tags": tags,
            "evidence_summary": "Evidência teste.",
            "human_review_required": True,
            "operational_recommendation_enabled": False,
            "composite_score_used": False,
        }

    def test_data_quality_precedes_epidemiology_queue(self):
        cards = pd.DataFrame([
            self.base_card("epidemiology_review|data_quality_review")
        ])
        out = build_operational_review_queue(cards, config())
        self.assertEqual(out.iloc[0]["review_queue"], "data_validation_first")
        self.assertTrue(bool(out.iloc[0]["queue_is_not_risk_rank"]))
        self.assertFalse(bool(out.iloc[0]["automatic_execution_enabled"]))

    def test_combined_epi_and_virology_gets_specific_queue(self):
        cards = pd.DataFrame([
            self.base_card("epidemiology_review|virology_review")
        ])
        out = build_operational_review_queue(cards, config())
        self.assertEqual(
            out.iloc[0]["review_queue"], "epidemiology_virology_review"
        )

    def test_state_summary_is_not_risk_rank(self):
        cards = pd.DataFrame([
            self.base_card("epidemiology_review")
        ])
        queue = build_operational_review_queue(cards, config())
        summary = build_state_review_summary(queue)
        self.assertTrue(summary["queue_is_not_risk_rank"])
        self.assertFalse(summary["automatic_execution_enabled"])


if __name__ == "__main__":
    unittest.main()
