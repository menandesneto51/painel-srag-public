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

from src.learning_action_followup_report_v2_17 import (
    build_learning_action_followup_summary,
    render_learning_action_followup_report,
)


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Gera relatório de follow-up das ações de aprendizado v2.17."
    )
    parser.add_argument(
        "--records",
        type=Path,
        default=ROOT / "data_candidate" / "learning_action_followup_v2_17" / "learning_action_followup_validated_v2_17.csv",
    )
    parser.add_argument(
        "--out-dir",
        type=Path,
        default=ROOT / "data_candidate" / "learning_action_followup_v2_17",
    )
    args = parser.parse_args()

    records = pd.read_csv(args.records) if args.records.exists() else None
    summary = build_learning_action_followup_summary(records)
    report = render_learning_action_followup_report(summary)

    args.out_dir.mkdir(parents=True, exist_ok=True)
    (args.out_dir / "learning_action_followup_summary_v2_17.json").write_text(
        json.dumps(summary, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    (args.out_dir / "learning_action_followup_report_v2_17.md").write_text(
        report,
        encoding="utf-8",
    )
    print(json.dumps(summary, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
