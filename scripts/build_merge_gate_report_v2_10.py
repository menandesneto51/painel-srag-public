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

from src.merge_gate_report_v2_10 import (
    render_merge_gate_report,
    summarize_merge_gate,
)


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Gera relatório do gate de merge v2.10."
    )
    parser.add_argument(
        "--records",
        type=Path,
        default=ROOT / "data_candidate" / "merge_gate_v2_10" / "merge_gate_validated_v2_10.csv",
    )
    parser.add_argument(
        "--out-dir",
        type=Path,
        default=ROOT / "data_candidate" / "merge_gate_v2_10",
    )
    args = parser.parse_args()

    if not args.records.exists():
        raise FileNotFoundError(args.records)

    records = pd.read_csv(args.records)
    summary = summarize_merge_gate(records)
    report = render_merge_gate_report(records)

    args.out_dir.mkdir(parents=True, exist_ok=True)
    (args.out_dir / "merge_gate_summary_v2_10.json").write_text(
        json.dumps(summary, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    (args.out_dir / "merge_gate_report_v2_10.md").write_text(
        report,
        encoding="utf-8",
    )

    print(json.dumps(summary, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
