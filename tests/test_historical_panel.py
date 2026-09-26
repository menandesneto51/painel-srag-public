# -*- coding: utf-8 -*-
import unittest

import pandas as pd

from scripts.build_historical_panel import densify_full_year
from src.epi_calendar import epidemiological_weeks_in_year


class HistoricalPanelTests(unittest.TestCase):
    def population(self):
        rows = [
            {"codigo_ibge": f"51{i:05d}", "municipio": f"Municipio {i}", "populacao": 1000 + i}
            for i in range(142)
        ]
        return pd.DataFrame(rows)

    def test_full_year_is_dense_and_zero_filled(self):
        population = self.population()
        observed = pd.DataFrame([
            {
                "codigo_ibge": population.iloc[0]["codigo_ibge"],
                "SE": 10,
                "casos": 2,
                "hospitalizacoes": 2,
                "uti": 1,
                "obitos": 0,
                "curas": 2,
            }
        ])
        year = 2025
        panel = densify_full_year(observed, population, year)
        weeks = epidemiological_weeks_in_year(year)

        self.assertEqual(len(panel), 142 * weeks)
        self.assertFalse(panel.duplicated(["ANO", "SE", "codigo_ibge"]).any())
        self.assertEqual(int(panel["casos"].sum()), 2)

        zero_row = panel.loc[
            (panel["codigo_ibge"] == population.iloc[0]["codigo_ibge"])
            & (panel["SE"] == 1)
        ].iloc[0]
        self.assertEqual(int(zero_row["casos"]), 0)
        self.assertEqual(float(zero_row["incidencia_srag_100k"]), 0.0)

    def test_population_key_is_preserved(self):
        population = self.population()
        panel = densify_full_year(pd.DataFrame(), population, 2024)
        self.assertEqual(panel["codigo_ibge"].nunique(), 142)


if __name__ == "__main__":
    unittest.main()
