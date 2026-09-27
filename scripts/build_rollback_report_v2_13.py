# -*- coding: utf-8 -*-
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.rollback_report_v2_13 import build_rollback_summary, render_rollback_report


def read_optional(path: Path):
    return pd.read_csv(path) if path.exists() else None


def main() -> int:
    parser = argparse.ArgumentParser(description="Gera relatório estadual de rollback v2.13.")
    parser.add_argument(
        "--decisions",
        type=Path,
        default=ROOT / "data_candidate" / "rollback_v2_13" / "human_rollback_decisions_validated_v2_13.csv",
    )
    parser.add_argument(
        "--executions",
        type=Path,
        default=ROOT / "data_candidate" / "rollback_v2_13" / "rollback_execution_validated_v2_13.csv",
    )
    parser.add_argument(
        "--out-dir",
        type=Path,
        default=ROOT / "data_candidate" / "rollback_v2_13",
    )
    args = parser.parse_args()

    summary = build_rollback_summary(
        read_optional(args.decisions),
        read_optional(args.executions),
    )
    report = render_rollback_report(summary)

    args.out_dir.mkdir(parents=True, exist_ok=True)
    (args.out_dir / "rollback_summary_v2_13.json").write_text(
        json.dumps(summary, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    (args.out_dir / "rollback_report_v2_13.md").write_text(
        report,
        encoding="utf-8",
    )
    print(json.dumps(summary, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
