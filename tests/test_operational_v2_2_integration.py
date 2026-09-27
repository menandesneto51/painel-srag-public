# -*- coding: utf-8 -*-
import unittest

import pandas as pd

from src.operational_actions import build_operational_action_suggestions
from src.operational_brief import build_operational_review_queues
from src.operational_review import build_operational_review_queue


class OperationalV22IntegrationTests(unittest.TestCase):
    def test_queue_and_actions_are_complementary(self):
        cards = pd.DataFrame([
            {
                "codigo_ibge": "5103403",
                "municipio": "Cuiabá",
                "review_tags": "epidemiology_review",
                "evidence_summary": "atividade acima do esperado",
                "human_review_required": True,
                "operational_recommendation_enabled": False,
                "composite_score_used": False,
            },
            {
                "codigo_ibge": "5108402",
                "municipio": "Várzea Grande",
                "review_tags": "",
                "evidence_summary": "sem destaque automático",
                "human_review_required": True,
                "operational_recommendation_enabled": False,
                "composite_score_used": False,
            },
        ])
        review_cfg = {
            "review_tag_actions": {
                "epidemiology_review": ["Revisar série temporal"]
            },
            "queue_rules": [
                {
                    "requires_any_tags": ["epidemiology_review"],
                    "queue": "epidemiology_review",
                    "description": "Revisão epidemiológica",
                },
                {
                    "queue": "routine_monitoring",
                    "description": "Monitoramento de rotina",
                },
            ],
        }
        queue = build_operational_review_queue(cards, review_cfg)
        self.assertEqual(len(queue), 2)
        self.assertTrue(queue["queue_is_not_risk_rank"].all())

        territorial = pd.DataFrame([
            {
                "codigo_ibge": "5103403",
                "municipio": "Cuiabá",
                "signal_status": "elevated_and_rising_experimental",
                "signal_confidence": "high_experimental",
                "silence_status": "activity_present",
                "virology_status": "not_available",
                "healthcare_pressure_available": False,
                "territorial_model_status": "under_calibration",
            },
            {
                "codigo_ibge": "5108402",
                "municipio": "Várzea Grande",
                "signal_status": "no_combined_signal_experimental",
                "signal_confidence": "high_experimental",
                "silence_status": "activity_present",
                "virology_status": "not_available",
                "healthcare_pressure_available": False,
                "territorial_model_status": "under_calibration",
            },
        ])
        matrix = {
            "sources": {},
            "actions": [{
                "action_id": "SURV-01",
                "domain": "surveillance",
                "title": "Revisar sinal",
                "trigger_tags_any": ["epidemiology_review"],
                "suggested_review_owner": "vigilancia",
                "suggested_timeframe": "revisao_atual",
                "action_text": "Revisar sinal.",
                "source_refs": [],
            }],
        }
        actions = build_operational_action_suggestions(
            territorial, cards, matrix
        )
        self.assertEqual(actions["codigo_ibge"].nunique(), 1)

        domain_queues = build_operational_review_queues(actions)
        self.assertEqual(len(domain_queues), 1)
        self.assertNotIn("score", domain_queues.columns)
        self.assertNotIn("rank", domain_queues.columns)


if __name__ == "__main__":
    unittest.main()
