# -*- coding: utf-8 -*-
import unittest

import pandas as pd

from src.candidate_rule_queue_v2_7 import (
    build_candidate_review_queue,
    validate_candidate_operational_config,
)


def config():
    return {
        "principles": {
            "queue_is_not_risk_rank": True,
            "no_automatic_action": True,
            "human_review_required": True,
            "patient_level_decisions_disabled": True,
            "composite_score_enabled": False,
        },
        "review_tag_actions": {
            "epidemiology_review": ["Revisar epidemiologia."]
        },
        "queue_rules": [
            {
                "queue": "epidemiology_review",
                "requires_any_tags": ["epidemiology_review"],
                "description": "Revisão epidemiológica.",
            },
            {
                "queue": "routine_monitoring",
                "description": "Rotina.",
            },
        ],
    }


def cards():
    rows = []
    for i in range(142):
        rows.append({
            "codigo_ibge": f"51{i:05d}",
            "municipio": f"Municipio {i}",
            "review_tags": "epidemiology_review" if i == 0 else "",
            "evidence_summary": "teste",
            "human_review_required": True,
            "operational_recommendation_enabled": False,
            "composite_score_used": False,
        })
    return pd.DataFrame(rows)


class CandidateRuleQueueV27Tests(unittest.TestCase):
    def test_candidate_queue_is_isolated_and_nonautomatic(self):
        out = build_candidate_review_queue(
            cards(),
            config(),
            proposal_id="prop_1",
            candidate_rule_version="candidate-1",
        )
        self.assertEqual(len(out), 142)
        self.assertTrue(out["candidate_only"].all())
        self.assertTrue(out["shadow_only"].all())
        self.assertFalse(out["automatic_activation_enabled"].any())
        self.assertFalse(out["automatic_rule_change_enabled"].any())

    def test_candidate_config_cannot_enable_composite_score(self):
        cfg = config()
        cfg["principles"]["composite_score_enabled"] = True
        with self.assertRaises(ValueError):
            validate_candidate_operational_config(cfg)

    def test_candidate_config_requires_routine_fallback(self):
        cfg = config()
        cfg["queue_rules"][-1]["queue"] = "epidemiology_review"
        with self.assertRaises(ValueError):
            validate_candidate_operational_config(cfg)


if __name__ == "__main__":
    unittest.main()
