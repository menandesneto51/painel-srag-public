# -*- coding: utf-8 -*-
import unittest

import pandas as pd

from src.decision_audit_report_v2_5 import (
    build_decision_audit_summary,
    render_decision_audit_markdown,
)


class DecisionAuditReportV25Tests(unittest.TestCase):
    def decisions(self):
        return pd.DataFrame([{
            "decision_record_id": "dec_1",
            "codigo_ibge": "5103403",
            "decision_scope": "queue",
            "reviewer_role": "epidemiologista",
            "decision_status": "continue_monitoring",
            "follow_up_required": True,
            "decision_recorded_by_human": True,
            "automatic_execution_enabled": False,
            "decision_is_not_proof_of_execution": True,
        }])

    def follow(self):
        return pd.DataFrame([{
            "decision_record_id": "dec_1",
            "follow_up_state": "open",
            "automatic_execution_enabled": False,
            "follow_up_state_is_not_risk": True,
        }])

    def test_summary_preserves_governance(self):
        summary = build_decision_audit_summary(
            self.decisions(), self.follow()
        )
        self.assertEqual(summary["decision_records"], 1)
        self.assertFalse(summary["automatic_execution_enabled"])
        self.assertTrue(summary["decision_is_not_proof_of_execution"])
        self.assertFalse(summary["personal_identifier_storage"])

    def test_report_states_decision_is_not_execution(self):
        report = render_decision_audit_markdown(
            self.decisions(), self.follow()
        )
        self.assertIn("não prova que uma ação externa foi executada", report)
        self.assertIn("Nenhum status de follow-up é classe de risco", report)


if __name__ == "__main__":
    unittest.main()
