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

from src.rule_change_evaluation_report_v2_8 import (
    render_rule_change_evaluation_report,
    summarize_rule_change_evaluations,
)


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Gera relatório estadual das avaliações de propostas v2.8."
    )
    parser.add_argument(
        "--evaluations",
        type=Path,
        default=ROOT / "data_candidate" / "rule_change_evaluation_v2_8" / "rule_change_evaluations_validated_v2_8.csv",
    )
    parser.add_argument(
        "--out-dir",
        type=Path,
        default=ROOT / "data_candidate" / "rule_change_evaluation_v2_8",
    )
    args = parser.parse_args()

    if not args.evaluations.exists():
        raise FileNotFoundError(args.evaluations)

    evaluations = pd.read_csv(args.evaluations)
    summary = summarize_rule_change_evaluations(evaluations)
    report = render_rule_change_evaluation_report(evaluations)

    args.out_dir.mkdir(parents=True, exist_ok=True)
    (args.out_dir / "rule_change_evaluation_summary_v2_8.json").write_text(
        json.dumps(summary, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    (args.out_dir / "rule_change_evaluation_report_v2_8.md").write_text(
        report,
        encoding="utf-8",
    )
    print(json.dumps(summary, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
