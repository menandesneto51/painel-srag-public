# -*- coding: utf-8 -*-
import re
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
APP = ROOT / "app_review_streamlit.py"


class ReviewAppStructureTests(unittest.TestCase):
    def test_tab_indices_are_unique_and_declared(self):
        content = APP.read_text(encoding="utf-8")
        indices = [int(x) for x in re.findall(r"with tabs\[(\d+)\]:", content)]
        self.assertEqual(len(indices), len(set(indices)))
        self.assertEqual(indices, sorted(indices))

        match = re.search(
            r"tabs\s*=\s*st\.tabs\(\[(.*?)\]\)",
            content,
            flags=re.DOTALL,
        )
        self.assertIsNotNone(match)
        labels = re.findall(r'"([^"]+)"', match.group(1))
        self.assertGreater(len(labels), 0)
        self.assertEqual(max(indices), len(labels) - 1)
        self.assertEqual(len(indices), len(labels))

    def test_v25_v26_v27_are_separate_tabs(self):
        content = APP.read_text(encoding="utf-8")
        self.assertIn("Auditoria humana v2.5", content)
        self.assertIn("Concordância workflow × decisão v2.6", content)
        self.assertIn("Propostas e modo sombra v2.7", content)
        self.assertEqual(content.count("with tabs[8]:"), 1)
        self.assertEqual(content.count("with tabs[9]:"), 1)
        self.assertEqual(content.count("with tabs[10]:"), 1)


if __name__ == "__main__":
    unittest.main()
