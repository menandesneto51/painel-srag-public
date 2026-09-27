# -*- coding: utf-8 -*-
import unittest

import pandas as pd

from src.governance_observability_v2_16 import (
    build_governance_observability_summary,
    build_proposal_governance_status,
    build_transition_metrics,
)


CONFIG = {
    "threshold_status": "experimental_internal_not_sla",
    "default_stale_threshold_hours": 168,
    "stage_stale_threshold_hours": {
        "merge_gate": 72,
        "effect_verification": 336,
    },
    "terminal_stages": ["effect_verification", "rollback_execution"],
}


class GovernanceObservabilityV216Tests(unittest.TestCase):
    def ledger(self):
        return pd.DataFrame([
            {
                "event_key": "proposal:p1",
                "stage_order": 10,
                "event_type": "proposal",
                "record_id": "p1",
                "parent_event_key": "",
                "event_at": "",
                "state": "draft",
                "proposal_id": "p1",
                "lineage_status": "linked_and_validated",
                "ledger_is_not_execution": True,
                "ledger_does_not_trigger_actions": True,
                "automatic_action_enabled": False,
            },
            {
                "event_key": "evaluation:e1",
                "stage_order": 20,
                "event_type": "evaluation",
                "record_id": "e1",
                "parent_event_key": "proposal:p1",
                "event_at": "2026-09-20T10:00:00Z",
                "state": "approved",
                "proposal_id": "p1",
                "lineage_status": "linked_and_validated",
                "ledger_is_not_execution": True,
                "ledger_does_not_trigger_actions": True,
                "automatic_action_enabled": False,
            },
            {
                "event_key": "implementation_package:i1",
                "stage_order": 30,
                "event_type": "implementation_package",
                "record_id": "i1",
                "parent_event_key": "evaluation:e1",
                "event_at": "2026-09-21T10:00:00Z",
                "state": "ready",
                "proposal_id": "p1",
                "lineage_status": "linked_and_validated",
                "ledger_is_not_execution": True,
                "ledger_does_not_trigger_actions": True,
                "automatic_action_enabled": False,
            },
            {
                "event_key": "merge_gate:m1",
                "stage_order": 40,
                "event_type": "merge_gate",
                "record_id": "m1",
                "parent_event_key": "implementation_package:i1",
                "event_at": "2026-09-22T10:00:00Z",
                "state": "eligible",
                "proposal_id": "p1",
                "lineage_status": "linked_and_validated",
                "ledger_is_not_execution": True,
                "ledger_does_not_trigger_actions": True,
                "automatic_action_enabled": False,
            },
            {
                "event_key": "proposal:p2",
                "stage_order": 10,
                "event_type": "proposal",
                "record_id": "p2",
                "parent_event_key": "",
                "event_at": "",
                "state": "draft",
                "proposal_id": "p2",
                "lineage_status": "linked_and_validated",
                "ledger_is_not_execution": True,
                "ledger_does_not_trigger_actions": True,
                "automatic_action_enabled": False,
            },
            {
                "event_key": "evaluation:e2",
                "stage_order": 20,
                "event_type": "evaluation",
                "record_id": "e2",
                "parent_event_key": "proposal:p2",
                "event_at": "2026-09-20T10:00:00Z",
                "state": "approved",
                "proposal_id": "p2",
                "lineage_status": "linked_and_validated",
                "ledger_is_not_execution": True,
                "ledger_does_not_trigger_actions": True,
                "automatic_action_enabled": False,
            },
            {
                "event_key": "effect_verification:f2",
                "stage_order": 100,
                "event_type": "effect_verification",
                "record_id": "f2",
                "parent_event_key": "evaluation:e2",
                "event_at": "2026-09-25T10:00:00Z",
                "state": "verified",
                "proposal_id": "p2",
                "lineage_status": "linked_and_validated",
                "ledger_is_not_execution": True,
                "ledger_does_not_trigger_actions": True,
                "automatic_action_enabled": False,
            },
        ])

    def test_transition_duration_is_computed(self):
        metrics = build_transition_metrics(self.ledger())
        row = metrics.loc[
            metrics["event_key"].eq("implementation_package:i1")
        ].iloc[0]
        self.assertEqual(row["transition_hours"], 24.0)
        self.assertFalse(bool(row["reviewer_score_enabled"]))
        self.assertFalse(bool(row["municipality_rank_enabled"]))

    def test_open_proposal_can_be_stale_but_not_risk(self):
        status = build_proposal_governance_status(
            self.ledger(),
            CONFIG,
            as_of="2026-09-26T12:00:00Z",
        )
        p1 = status.loc[status["proposal_id"].eq("p1")].iloc[0]
        self.assertTrue(bool(p1["stale_experimental"]))
        self.assertFalse(bool(p1["terminal_stage"]))
        self.assertTrue(bool(p1["stale_flag_is_not_risk"]))
        self.assertEqual(
            p1["threshold_status"],
            "experimental_internal_not_sla",
        )

    def test_terminal_stage_is_not_marked_stale(self):
        status = build_proposal_governance_status(
            self.ledger(),
            CONFIG,
            as_of="2026-10-30T12:00:00Z",
        )
        p2 = status.loc[status["proposal_id"].eq("p2")].iloc[0]
        self.assertTrue(bool(p2["terminal_stage"]))
        self.assertFalse(bool(p2["stale_experimental"]))

    def test_summary_never_scores_people_or_places(self):
        status = build_proposal_governance_status(
            self.ledger(),
            CONFIG,
            as_of="2026-09-26T12:00:00Z",
        )
        transitions = build_transition_metrics(self.ledger())
        summary = build_governance_observability_summary(
            status,
            transitions,
        )
        self.assertFalse(summary["reviewer_scoring"])
        self.assertFalse(summary["municipality_ranking"])
        self.assertFalse(summary["stale_flag_is_risk"])
        self.assertFalse(summary["thresholds_are_institutional_sla"])
        self.assertFalse(summary["automatic_action"])

    def test_as_of_before_last_event_is_rejected(self):
        with self.assertRaises(ValueError):
            build_proposal_governance_status(
                self.ledger(),
                CONFIG,
                as_of="2026-09-21T12:00:00Z",
            )


if __name__ == "__main__":
    unittest.main()
