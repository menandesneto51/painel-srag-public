# -*- coding: utf-8 -*-
import unittest

import pandas as pd

from src.healthcare_pressure_bridge import sanitize_healthcare_pressure


class HealthcarePressureBridgeTests(unittest.TestCase):
    def valid(self):
        return pd.DataFrame([{
            "codigo_ibge": "5103403",
            "reference_week": 20,
            "pressure_status": "high",
            "validation_status": "validated",
            "source_scope": "institutional",
            "hospital_occupancy_percent": 85.0,
            "open_requests": 12,
        }])

    def test_valid_aggregate_contract_passes(self):
        out = sanitize_healthcare_pressure(self.valid(), stable_week=20)
        self.assertEqual(out.iloc[0]["sanitization_status"], "aggregate_contract_passed")
        self.assertFalse(bool(out.iloc[0]["patient_level_fields_present"]))
        self.assertFalse(
            bool(out.iloc[0]["automatic_pressure_classification_enabled"])
        )

    def test_patient_identifier_column_is_rejected(self):
        frame = self.valid()
        frame["CPF"] = "00000000000"
        with self.assertRaises(ValueError):
            sanitize_healthcare_pressure(frame, stable_week=20)

    def test_unexpected_column_is_rejected(self):
        frame = self.valid()
        frame["internal_note_free_text"] = "x"
        with self.assertRaises(ValueError):
            sanitize_healthcare_pressure(frame, stable_week=20)

    def test_week_mismatch_is_rejected(self):
        with self.assertRaises(ValueError):
            sanitize_healthcare_pressure(self.valid(), stable_week=21)

    def test_percent_out_of_range_is_rejected(self):
        frame = self.valid()
        frame.loc[0, "hospital_occupancy_percent"] = 130
        with self.assertRaises(ValueError):
            sanitize_healthcare_pressure(frame, stable_week=20)


if __name__ == "__main__":
    unittest.main()
