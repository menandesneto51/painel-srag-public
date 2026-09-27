# -*- coding: utf-8 -*-
import unittest

import pandas as pd

from src.operational_stability import analyze_operational_stability


def make_snapshot(snapshot_id, overrides=None):
    overrides = overrides or {}
    rows = []
    for i in range(142):
        code = f"51{i:05d}"
        queue = overrides.get(code, "routine_monitoring")
        tags = "" if queue == "routine_monitoring" else "epidemiology_review"
        rows.append({
            "codigo_ibge": code,
            "municipio": f"Municipio {i}",
            "review_queue": queue,
            "review_tags": tags,
            "human_review_required": True,
            "automatic_execution_enabled": False,
            "queue_is_not_risk_rank": True,
        })
    return snapshot_id, pd.DataFrame(rows)


class OperationalStabilityTests(unittest.TestCase):
    def test_persistent_same_queue_and_new_entry(self):
        snapshots = [
            make_snapshot("s1"),
            make_snapshot("s2", {
                "5100000": "epidemiology_review",
                "5100001": "epidemiology_review",
            }),
            make_snapshot("s3", {
                "5100000": "epidemiology_review",
                "5100001": "routine_monitoring",
                "5100002": "laboratory_review",
            }),
            make_snapshot("s4", {
                "5100000": "epidemiology_review",
                "5100002": "laboratory_review",
                "5100003": "epidemiology_review",
            }),
        ]
        out = analyze_operational_stability(snapshots)
        rows = out.set_index("codigo_ibge")

        self.assertEqual(
            rows.loc["5100000", "workflow_pattern"],
            "persistent_same_queue",
        )
        self.assertTrue(
            bool(rows.loc["5100000", "sustained_3plus_cycles"])
        )
        self.assertEqual(
            rows.loc["5100003", "workflow_pattern"],
            "newly_entered_review",
        )
        self.assertTrue(out["workflow_stability_is_not_risk"].all())
        self.assertFalse(out["automatic_action_enabled"].any())

    def test_single_cycle_reversion(self):
        snapshots = [
            make_snapshot("s1"),
            make_snapshot("s2", {"5100000": "epidemiology_review"}),
            make_snapshot("s3"),
        ]
        out = analyze_operational_stability(snapshots)
        row = out.set_index("codigo_ibge").loc["5100000"]
        self.assertEqual(
            row["workflow_pattern"],
            "single_cycle_reversion",
        )
        self.assertEqual(
            int(row["single_cycle_reversion_count"]),
            1,
        )

    def test_changed_queue_while_persistent_nonroutine(self):
        snapshots = [
            make_snapshot("s1", {"5100000": "epidemiology_review"}),
            make_snapshot("s2", {"5100000": "epidemiology_review"}),
            make_snapshot("s3", {"5100000": "laboratory_review"}),
        ]
        out = analyze_operational_stability(snapshots)
        row = out.set_index("codigo_ibge").loc["5100000"]
        self.assertEqual(
            row["workflow_pattern"],
            "persistent_nonroutine_changed_queue",
        )
        self.assertEqual(int(row["current_nonroutine_run"]), 3)


if __name__ == "__main__":
    unittest.main()
