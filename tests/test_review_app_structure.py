# -*- coding: utf-8 -*-
import re
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
APP = ROOT / "app_review_streamlit.py"


class ReviewAppStructureTests(unittest.TestCase):
    def test_tab_indices_are_unique(self):
        content = APP.read_text(encoding="utf-8")
        indices = [int(x) for x in re.findall(r"with tabs\[(\d+)\]:", content)]
        self.assertEqual(len(indices), len(set(indices)))
        self.assertEqual(indices, sorted(indices))

    def test_v25_and_v26_are_separate_tabs(self):
        content = APP.read_text(encoding="utf-8")
        self.assertIn("Auditoria humana v2.5", content)
        self.assertIn("Concordância workflow × decisão v2.6", content)
        self.assertEqual(content.count("with tabs[8]:"), 1)
        self.assertEqual(content.count("with tabs[9]:"), 1)


if __name__ == "__main__":
    unittest.main()
