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

from src.human_merge_report_v2_11 import (
    render_human_merge_cycle_report,
    summarize_human_merge_cycle,
)


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Gera relatório do ciclo humano de merge v2.11."
    )
    parser.add_argument(
        "--decisions",
        type=Path,
        default=(
            ROOT
            / "data_candidate"
            / "human_merge_v2_11"
            / "human_merge_decisions_validated_v2_11.csv"
        ),
    )
    parser.add_argument(
        "--post-merge",
        type=Path,
        default=(
            ROOT
            / "data_candidate"
            / "human_merge_v2_11"
            / "post_merge_records_validated_v2_11.csv"
        ),
    )
    parser.add_argument(
        "--out-dir",
        type=Path,
        default=ROOT / "data_candidate" / "human_merge_v2_11",
    )
    args = parser.parse_args()

    if not args.decisions.exists():
        raise FileNotFoundError(args.decisions)

    decisions = pd.read_csv(args.decisions)
    post_merge = (
        pd.read_csv(args.post_merge)
        if args.post_merge.exists()
        else None
    )

    summary = summarize_human_merge_cycle(
        decisions,
        post_merge,
    )
    report = render_human_merge_cycle_report(
        decisions,
        post_merge,
    )

    args.out_dir.mkdir(parents=True, exist_ok=True)
    (args.out_dir / "human_merge_summary_v2_11.json").write_text(
        json.dumps(summary, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    (args.out_dir / "human_merge_report_v2_11.md").write_text(
        report,
        encoding="utf-8",
    )

    print(json.dumps(summary, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
