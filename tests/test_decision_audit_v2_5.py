# -*- coding: utf-8 -*-
import unittest

import pandas as pd

from src.decision_audit_v2_5 import validate_decision_audit
from src.decision_followup_v2_5 import (
    build_follow_up_status,
    validate_follow_up_events,
)


CONFIG = {
    "decision_scopes": ["queue", "action"],
    "decision_statuses": [
        "continue_monitoring",
        "request_epi_investigation",
    ],
    "follow_up_event_statuses": [
        "acknowledged",
        "in_progress",
        "completed",
        "cancelled",
    ],
}


class DecisionAuditV25Tests(unittest.TestCase):
    def queue(self):
        return pd.DataFrame([{
            "codigo_ibge": "5103403",
            "municipio": "Cuiabá",
            "review_queue": "epidemiology_review",
        }])

    def actions(self):
        return pd.DataFrame([{
            "codigo_ibge": "5103403",
            "action_id": "SURV-01",
        }])

    def decision(self):
        return pd.DataFrame([{
            "codigo_ibge": "5103403",
            "municipio": "Cuiabá",
            "snapshot_id": "srag-mt-2026-se20",
            "review_queue": "epidemiology_review",
            "decision_scope": "action",
            "action_id": "SURV-01",
            "reviewed_at": "2026-09-27T08:00:00-04:00",
            "reviewer_role": "epidemiologista",
            "decision_status": "request_epi_investigation",
            "rationale": "Sinal persistente e coerente com a revisão territorial.",
            "evidence_refs": "combined_signals;virology",
            "follow_up_required": True,
            "follow_up_due_at": "2026-09-29T08:00:00-04:00",
            "follow_up_owner_role": "vigilancia_epidemiologica",
        }])

    def test_decision_is_linked_and_never_executes(self):
        out = validate_decision_audit(
            self.decision(), self.queue(), self.actions(), CONFIG
        )
        row = out.iloc[0]
        self.assertTrue(str(row["decision_record_id"]).startswith("dec_"))
        self.assertFalse(bool(row["automatic_execution_enabled"]))
        self.assertFalse(bool(row["patient_level_decision_enabled"]))
        self.assertFalse(bool(row["clinical_prescription_enabled"]))
        self.assertTrue(bool(row["decision_is_not_proof_of_execution"]))

    def test_action_scope_requires_existing_action(self):
        decision = self.decision()
        decision.loc[0, "action_id"] = "UNKNOWN"
        with self.assertRaises(ValueError):
            validate_decision_audit(
                decision, self.queue(), self.actions(), CONFIG
            )

    def test_follow_up_required_needs_future_due_date(self):
        decision = self.decision()
        decision.loc[0, "follow_up_due_at"] = "2026-09-26T08:00:00-04:00"
        with self.assertRaises(ValueError):
            validate_decision_audit(
                decision, self.queue(), self.actions(), CONFIG
            )

    def test_follow_up_event_and_status(self):
        decisions = validate_decision_audit(
            self.decision(), self.queue(), self.actions(), CONFIG
        )
        decision_id = decisions.iloc[0]["decision_record_id"]
        events = pd.DataFrame([{
            "decision_record_id": decision_id,
            "event_at": "2026-09-28T10:00:00-04:00",
            "reviewer_role": "epidemiologista",
            "follow_up_event_status": "in_progress",
            "follow_up_note": "Revisão municipal iniciada.",
        }])
        validated_events = validate_follow_up_events(
            events,
            decisions,
            set(CONFIG["follow_up_event_statuses"]),
        )
        status = build_follow_up_status(
            decisions,
            validated_events,
            as_of="2026-09-30T12:00:00-04:00",
        )
        self.assertEqual(status.iloc[0]["follow_up_state"], "overdue")
        self.assertFalse(bool(status.iloc[0]["automatic_execution_enabled"]))
        self.assertTrue(bool(status.iloc[0]["follow_up_state_is_not_risk"]))


if __name__ == "__main__":
    unittest.main()
