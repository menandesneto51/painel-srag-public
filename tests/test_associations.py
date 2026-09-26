# -*- coding: utf-8 -*-
import unittest

from src.associations import crude_or


class AssociationTests(unittest.TestCase):
    def test_crude_or_known_table(self):
        result = crude_or(20, 80, 10, 90)
        self.assertAlmostEqual(result["or"], 2.25)
        self.assertLess(result["ic95_inf"], result["or"])
        self.assertGreater(result["ic95_sup"], result["or"])
        self.assertFalse(result["zero_cell_correction"])

    def test_zero_cell_uses_correction(self):
        result = crude_or(0, 10, 5, 20)
        self.assertTrue(result["zero_cell_correction"])
        self.assertGreater(result["or"], 0)
        self.assertGreater(result["ic95_sup"], result["ic95_inf"])


if __name__ == "__main__":
    unittest.main()
