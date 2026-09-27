# -*- coding: utf-8 -*-
import unittest

import pandas as pd

from src.change_lifecycle_report_v2_15 import (
    build_change_lifecycle_metadata,
    render_change_lifecycle_report,
)


class ChangeLifecycleReportV215Tests(unittest.TestCase):
    def frame(self):
        return pd.DataFrame([
            {
                "event_key": "proposal:p1",
                "stage_order": 10,
                "event_type": "proposal",
                "record_id": "p1",
                "parent_event_key": "",
                "parent_event_type": "",
                "parent_record_id": "",
                "event_at": "",
                "state": "ready",
                "proposal_id": "p1",
                "implementation_package_id": "",
                "commit_sha": "",
                "environment": "",
                "lineage_status": "linked_and_validated",
                "ledger_is_not_execution": True,
                "ledger_does_not_trigger_actions": True,
                "automatic_action_enabled": False,
                "human_review_required": True,
            },
            {
                "event_key": "evaluation:e1",
                "stage_order": 20,
                "event_type": "evaluation",
                "record_id": "e1",
                "parent_event_key": "proposal:p1",
                "parent_event_type": "proposal",
                "parent_record_id": "p1",
                "event_at": "2026-09-27T10:00:00Z",
                "state": "approve",
                "proposal_id": "p1",
                "implementation_package_id": "",
                "commit_sha": "",
                "environment": "",
                "lineage_status": "linked_and_validated",
                "ledger_is_not_execution": True,
                "ledger_does_not_trigger_actions": True,
                "automatic_action_enabled": False,
                "human_review_required": True,
            },
        ])

    def test_metadata_marks_integrity_validated(self):
        metadata = build_change_lifecycle_metadata(self.frame())
        self.assertEqual(metadata["events"], 2)
        self.assertTrue(metadata["chronology_validated"])
        self.assertTrue(metadata["parent_child_integrity_validated"])
        self.assertFalse(metadata["automatic_action_enabled"])

    def test_report_states_observational_nature(self):
        report = render_change_lifecycle_report(self.frame())
        self.assertIn("Ledger observacional e auditável", report)
        self.assertIn("não dispara ações", report)


if __name__ == "__main__":
    unittest.main()
