from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path
import unittest


REPO_ROOT = Path(__file__).resolve().parents[1]
LAUNCHER = REPO_ROOT / "scripts" / "catalogo_ses.py"


class CatalogLauncherTests(unittest.TestCase):
    def test_self_test_runs_in_clean_checkout(self) -> None:
        completed = subprocess.run(
            [sys.executable, str(LAUNCHER), "--self-test"],
            check=False,
            capture_output=True,
            text=True,
        )
        self.assertEqual(completed.returncode, 0, completed.stderr)
        payload = json.loads(completed.stdout)
        self.assertEqual(payload["status"], "launcher_ready")
        self.assertFalse(payload["preflight_complete"])


if __name__ == "__main__":
    unittest.main()
