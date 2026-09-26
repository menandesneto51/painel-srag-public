# -*- coding: utf-8 -*-
import json
import tempfile
import unittest
from pathlib import Path

import pandas as pd

from src.vintage_backtest import backtest_metric


class VintageBacktestTests(unittest.TestCase):
    def write_vintage(self, root: Path, day: str, values: dict[int, int]):
        folder = root / day
        folder.mkdir(parents=True)
        pd.DataFrame(
            [{"SE": week, "casos": value} for week, value in values.items()]
        ).to_csv(folder / "weekly.csv", index=False)
        (folder / "metadata.json").write_text(
            json.dumps({"vintage_date": day, "reference_year": 2026}),
            encoding="utf-8",
        )

    def test_backtest_detects_revision_by_age(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self.write_vintage(root, "2026-03-15", {9: 90, 10: 50})
            self.write_vintage(root, "2026-03-22", {9: 100, 10: 90, 11: 40})
            self.write_vintage(root, "2026-03-29", {9: 100, 10: 100, 11: 80})

            detail, summary, report = backtest_metric(
                root, "casos", tolerance=0.15, min_observations=2
            )

            self.assertFalse(detail.empty)
            self.assertFalse(summary.empty)
            self.assertEqual(report["vintage_count"], 3)
            self.assertEqual(report["reference_vintage_date"], "2026-03-29")
            self.assertIn(report["status"], {"calibrated_candidate", "insufficient_stability"})


if __name__ == "__main__":
    unittest.main()
