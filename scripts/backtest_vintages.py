# -*- coding: utf-8 -*-
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.vintage_backtest import backtest_metric


def main() -> int:
    parser = argparse.ArgumentParser(description="Backtesting de revisão semanal por vintages agregados.")
    parser.add_argument("--metric", default="casos")
    parser.add_argument("--vintages", type=Path, default=ROOT / "vintages" / "sivep")
    parser.add_argument("--tolerance", type=float, default=0.05)
    parser.add_argument("--min-observations", type=int, default=5)
    parser.add_argument("--out-dir", type=Path, default=ROOT / "reports" / "stability")
    args = parser.parse_args()

    detail, summary, report = backtest_metric(
        args.vintages,
        args.metric,
        tolerance=args.tolerance,
        min_observations=args.min_observations,
    )
    args.out_dir.mkdir(parents=True, exist_ok=True)
    detail.to_csv(args.out_dir / f"{args.metric}_vintage_detail.csv", index=False)
    summary.to_csv(args.out_dir / f"{args.metric}_vintage_summary.csv", index=False)
    (args.out_dir / f"{args.metric}_vintage_report.json").write_text(
        json.dumps(report, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
