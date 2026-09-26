# -*- coding: utf-8 -*-
import unittest

import pandas as pd

from src.epi_calendar import epidemiological_weeks_in_year
from src.baseline_signals import (
    add_anomaly_signal,
    build_seasonal_baseline,
    build_trend_signals,
    combine_surveillance_signals,
)


def make_history():
    rows = []
    for year in (2022, 2023, 2024, 2025):
        for week in range(1, epidemiological_weeks_in_year(year) + 1):
            rows.append({
                "ANO": year,
                "SE": week,
                "codigo_ibge": "5103403",
                "municipio": "Cuiabá",
                "populacao": 700000,
                "casos": 10,
                "hospitalizacoes": 7,
                "uti": 2,
                "obitos": 1,
            })

    current_hosp = [7, 7, 7, 7, 7, 7, 7, 7, 7, 7, 21, 28]
    for week, hosp in enumerate(current_hosp, start=1):
        rows.append({
            "ANO": 2026,
            "SE": week,
            "codigo_ibge": "5103403",
            "municipio": "Cuiabá",
            "populacao": 700000,
            "casos": hosp + 3,
            "hospitalizacoes": hosp,
            "uti": 2,
            "obitos": 1,
        })
    return pd.DataFrame(rows)


class BaselineSignalTests(unittest.TestCase):
    def test_baseline_has_53_weeks(self):
        baseline = build_seasonal_baseline(
            make_history(),
            metric="hospitalizacoes",
            target_year=2026,
            min_years=3,
            week_window=2,
            history_years=[2023, 2024, 2025],
        )
        self.assertEqual(len(baseline), 53)
        self.assertTrue((baseline["baseline_status"] == "experimental").all())

    def test_trend_detects_rising_recent_window(self):
        trends = build_trend_signals(
            make_history(),
            metric="hospitalizacoes",
            stable_week=12,
            recent_weeks=2,
            previous_weeks=2,
            pseudocount=0.5,
        )
        row = trends.iloc[0]
        self.assertEqual(row["trend_status"], "experimental")
        self.assertGreater(row["trend_ratio"], 1.0)
        self.assertGreater(row["trend_log2"], 0.0)

    def test_rate_baseline_requires_annual_denominator(self):
        history = make_history()
        history["ano_populacao"] = 2026
        with self.assertRaises(ValueError):
            build_seasonal_baseline(
                history,
                metric="hospitalizacao_100k",
                target_year=2026,
                min_years=3,
                week_window=2,
                history_years=[2023, 2024, 2025],
            )

    def test_anomaly_is_not_operational_alert(self):
        history = make_history()
        baseline = build_seasonal_baseline(
            history,
            metric="hospitalizacoes",
            target_year=2026,
            min_years=3,
            week_window=2,
            history_years=[2023, 2024, 2025],
        )
        anomalies = add_anomaly_signal(
            history,
            baseline,
            metric="hospitalizacoes",
            stable_week=12,
            robust_z_threshold=3.5,
        )
        trends = build_trend_signals(
            history,
            metric="hospitalizacoes",
            stable_week=12,
        )
        combined = combine_surveillance_signals(anomalies, trends)
        self.assertFalse(combined["validated_for_operational_alert"].any())
        week12 = combined.loc[combined["SE"] == 12].iloc[0]
        self.assertTrue(str(week12["anomaly_status"]).startswith("above_expected"))
        self.assertEqual(week12["signal_status"], "elevated_and_rising_experimental")


if __name__ == "__main__":
    unittest.main()
