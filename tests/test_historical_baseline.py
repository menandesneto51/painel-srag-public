# -*- coding: utf-8 -*-
import unittest

import pandas as pd

from src.historical_baseline import robust_weekly_baseline


class HistoricalBaselineTests(unittest.TestCase):
    def test_requires_three_explicit_years(self):
        df = pd.DataFrame({
            "ano": [2023, 2024],
            "SE": [1, 1],
            "casos": [10, 12],
        })
        with self.assertRaises(ValueError):
            robust_weekly_baseline(df, "casos", [2023, 2024])

    def test_robust_statistics_by_week(self):
        df = pd.DataFrame({
            "ano": [2023, 2024, 2025, 2023, 2024, 2025],
            "SE": [1, 1, 1, 2, 2, 2],
            "casos": [10, 12, 100, 20, 22, 24],
        })
        baseline = robust_weekly_baseline(df, "casos", [2023, 2024, 2025])
        se1 = baseline.loc[baseline["SE"] == 1].iloc[0]
        se2 = baseline.loc[baseline["SE"] == 2].iloc[0]

        self.assertEqual(float(se1["median"]), 12.0)
        self.assertEqual(int(se1["n_years"]), 3)
        self.assertEqual(float(se2["median"]), 22.0)
        self.assertEqual(float(se2["mad"]), 2.0)


if __name__ == "__main__":
    unittest.main()
