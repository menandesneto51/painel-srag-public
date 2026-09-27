# -*- coding: utf-8 -*-
import unittest
import pandas as pd
from src.rule_change_proposals_report_v2_7 import (
    render_rule_change_proposals_report,
    summarize_rule_change_proposals,
)

class RuleChangeProposalReportV27Tests(unittest.TestCase):
    def frame(self):
        return pd.DataFrame([{
            "proposal_id":"prop_1",
            "rule_key":"review_queue::epidemiology_review",
            "workflow_alignment":"nonroutine_not_escalated_rule_review",
            "affected_records":2,
            "affected_municipalities":2,
            "example_municipalities":"Cuiabá | Várzea Grande",
            "proposal_type":"queue_rule",
            "proposal_status":"draft",
            "problem_statement":"Regra possivelmente sensível.",
            "analysis_required":"case_review|epidemiology_review|backtest|documentation",
            "automatic_rule_change_enabled":False,
            "automatic_threshold_change_enabled":False,
            "proposal_is_not_change":True,
            "human_approval_required":True,
        }])

    def test_summary_preserves_governance(self):
        s=summarize_rule_change_proposals(self.frame())
        self.assertEqual(s["proposals"],1)
        self.assertFalse(s["automatic_rule_change"])
        self.assertFalse(s["automatic_threshold_change"])
        self.assertTrue(s["human_approval_required"])

    def test_report_states_proposal_is_not_change(self):
        report=render_rule_change_proposals_report(self.frame())
        self.assertIn("Proposta não é mudança aplicada",report)
        self.assertIn("Nenhuma regra ou threshold é alterado automaticamente",report)

if __name__=="__main__":
    unittest.main()
