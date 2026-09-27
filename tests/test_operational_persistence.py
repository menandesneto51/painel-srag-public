# -*- coding: utf-8 -*-
import unittest

import pandas as pd

from src.operational_persistence import compare_operational_vintages


def make_queue(overrides=None):
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
    return pd.DataFrame(rows)


class OperationalPersistenceTests(unittest.TestCase):
    def test_enter_persist_change_and_resolve(self):
        prev = make_queue({
            "5100000": "routine_monitoring",
            "5100001": "epidemiology_review",
            "5100002": "epidemiology_review",
            "5100003": "laboratory_review",
        })
        cur = make_queue({
            "5100000": "epidemiology_review",
            "5100001": "epidemiology_review",
            "5100002": "routine_monitoring",
            "5100003": "multidisciplinary_review",
        })
        out = compare_operational_vintages(cur, prev)
        states = out.set_index("codigo_ibge")["change_state"].to_dict()
        self.assertEqual(states["5100000"], "entered_review")
        self.assertEqual(states["5100001"], "persistent_same_queue")
        self.assertEqual(states["5100002"], "returned_to_routine")
        self.assertEqual(states["5100003"], "changed_review_queue")
        self.assertTrue(out["change_state_is_not_risk"].all())
        self.assertTrue(out["persistence_is_not_severity"].all())
        self.assertFalse(out["automatic_action_enabled"].any())

    def test_first_snapshot_is_baseline_only(self):
        cur = make_queue({"5100000": "epidemiology_review"})
        out = compare_operational_vintages(cur, None)
        states = out.set_index("codigo_ibge")["change_state"].to_dict()
        self.assertEqual(states["5100000"], "baseline_snapshot_nonroutine")
        self.assertEqual(states["5100001"], "baseline_snapshot_routine")


if __name__ == "__main__":
    unittest.main()
