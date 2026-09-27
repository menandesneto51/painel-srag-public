# -*- coding: utf-8 -*-
import unittest

import pandas as pd

from src.rule_change_proposals_v2_7 import (
    build_rule_change_proposals,
    validate_proposal_registry,
)


class RuleChangeProposalsV27Tests(unittest.TestCase):
    def concordance(self):
        return pd.DataFrame([
            {
                "decision_record_id": "d1",
                "codigo_ibge": "5103403",
                "municipio": "Cuiabá",
                "review_queue": "epidemiology_review",
                "decision_status": "continue_monitoring",
                "workflow_alignment": "nonroutine_not_escalated_rule_review",
                "rule_review_required": True,
            },
            {
                "decision_record_id": "d2",
                "codigo_ibge": "5108402",
                "municipio": "Várzea Grande",
                "review_queue": "epidemiology_review",
                "decision_status": "continue_monitoring",
                "workflow_alignment": "nonroutine_not_escalated_rule_review",
                "rule_review_required": True,
            },
        ])

    def test_discordance_generates_proposal_not_change(self):
        proposals = build_rule_change_proposals(self.concordance())
        self.assertEqual(len(proposals), 1)
        row = proposals.iloc[0]
        self.assertEqual(int(row["affected_municipalities"]), 2)
        self.assertTrue(bool(row["proposal_is_not_change"]))
        self.assertTrue(bool(row["human_approval_required"]))
        self.assertFalse(bool(row["automatic_rule_change_enabled"]))

    def test_registry_rejects_auto_change(self):
        proposals = build_rule_change_proposals(self.concordance())
        proposals.loc[0, "automatic_rule_change_enabled"] = True
        with self.assertRaises(ValueError):
            validate_proposal_registry(
                proposals,
                allowed_statuses={"draft"},
                allowed_change_types={"queue_rule"},
            )


if __name__ == "__main__":
    unittest.main()
