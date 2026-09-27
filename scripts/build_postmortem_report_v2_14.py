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

from src.postmortem_report_v2_14 import (
    build_postmortem_summary,
    render_postmortem_report,
)


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Gera relatório estadual de post-mortem v2.14."
    )
    parser.add_argument(
        "--records",
        type=Path,
        default=ROOT / "data_candidate" / "postmortem_v2_14" / "postmortem_validated_v2_14.csv",
    )
    parser.add_argument(
        "--out-dir",
        type=Path,
        default=ROOT / "data_candidate" / "postmortem_v2_14",
    )
    args = parser.parse_args()

    records = pd.read_csv(args.records) if args.records.exists() else None
    summary = build_postmortem_summary(records)
    report = render_postmortem_report(summary)

    args.out_dir.mkdir(parents=True, exist_ok=True)
    (args.out_dir / "postmortem_summary_v2_14.json").write_text(
        json.dumps(summary, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    (args.out_dir / "postmortem_report_v2_14.md").write_text(
        report,
        encoding="utf-8",
    )
    print(json.dumps(summary, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
