# -*- coding: utf-8 -*-
import unittest

import pandas as pd

from src.epi_calendar import epidemiological_weeks_in_year
from src.p2_backtest import backtest_anomaly_thresholds


def synthetic_panel():
    rows = []
    for year in range(2019, 2026):
        weeks = epidemiological_weeks_in_year(year)
        for week in range(1, weeks + 1):
            base = 2
            if year >= 2023 and week in {20, 21, 22}:
                base = 10 + (year - 2023)
            rows.append({
                "ANO": year,
                "SE": week,
                "codigo_ibge": "5103403",
                "municipio": "Cuiabá",
                "populacao": 700000,
                "casos": base + 2,
                "hospitalizacoes": base,
                "uti": 1,
                "obitos": 0,
            })
    return pd.DataFrame(rows)


class P2BacktestTests(unittest.TestCase):
    def test_backtest_produces_threshold_metrics(self):
        result = backtest_anomaly_thresholds(
            synthetic_panel(),
            metric="hospitalizacoes",
            min_training_years=3,
            week_window=2,
            thresholds=[2.5, 3.5],
            future_window_weeks=2,
            event_quantile=0.9,
        )
        self.assertEqual(set(result.summary["robust_z_threshold"]), {2.5, 3.5})
        self.assertGreater(len(result.predictions), 0)
        self.assertTrue(
            (result.summary["backtest_status"] == "experimental_internal_calibration").all()
        )

    def test_invalid_event_quantile_is_rejected(self):
        with self.assertRaises(ValueError):
            backtest_anomaly_thresholds(
                synthetic_panel(),
                event_quantile=1.0,
            )


if __name__ == "__main__":
    unittest.main()
