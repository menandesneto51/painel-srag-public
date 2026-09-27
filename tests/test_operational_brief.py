# -*- coding: utf-8 -*-
import unittest

import pandas as pd

from src.operational_brief import (
    build_operational_review_queues,
    build_state_operational_brief,
)


def actions():
    return pd.DataFrame([
        {
            "codigo_ibge": "5103403",
            "municipio": "Cuiabá",
            "action_id": "SURV-01",
            "domain": "surveillance",
            "title": "Validar sinal",
            "suggested_review_owner": "vigilancia",
            "suggested_timeframe": "priorizar_na_revisao_atual",
            "suggestion_status": "suggested_for_human_review",
            "human_review_required": True,
            "automatic_execution": False,
            "signal_confidence": "high_experimental",
        },
        {
            "codigo_ibge": "5108402",
            "municipio": "Várzea Grande",
            "action_id": "SURV-01",
            "domain": "surveillance",
            "title": "Validar sinal",
            "suggested_review_owner": "vigilancia",
            "suggested_timeframe": "priorizar_na_revisao_atual",
            "suggestion_status": "suggested_for_human_review",
            "human_review_required": True,
            "automatic_execution": False,
            "signal_confidence": "moderate_experimental",
        },
    ])


class OperationalBriefTests(unittest.TestCase):
    def test_queue_groups_without_ranking_municipalities(self):
        queues = build_operational_review_queues(actions())
        self.assertEqual(len(queues), 1)
        self.assertEqual(int(queues.iloc[0]["municipalities"]), 2)
        self.assertNotIn("rank", queues.columns)
        self.assertNotIn("score", queues.columns)

    def test_brief_states_governance(self):
        queues = build_operational_review_queues(actions())
        brief = build_state_operational_brief(actions(), queues, reference_week=20)
        self.assertIn("SE 20", brief)
        self.assertIn("Nenhuma ação é executada automaticamente", brief)
        self.assertIn("não usa score composto", brief)

    def test_automatic_execution_is_rejected(self):
        bad = actions()
        bad.loc[0, "automatic_execution"] = True
        with self.assertRaises(ValueError):
            build_operational_review_queues(bad)


if __name__ == "__main__":
    unittest.main()
