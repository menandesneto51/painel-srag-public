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

from src.p2_backtest import backtest_anomaly_thresholds


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Backtesting retrospectivo experimental dos sinais P2."
    )
    parser.add_argument(
        "--history",
        type=Path,
        default=ROOT / "data_candidate" / "history" / "municipal_weekly_history.csv",
    )
    parser.add_argument(
        "--config",
        type=Path,
        default=ROOT / "config" / "p2_backtest.json",
    )
    parser.add_argument(
        "--out-dir",
        type=Path,
        default=ROOT / "data_candidate" / "backtest",
    )
    args = parser.parse_args()

    cfg = json.loads(args.config.read_text(encoding="utf-8"))
    panel = pd.read_csv(args.history, dtype={"codigo_ibge": "string"})

    result = backtest_anomaly_thresholds(
        panel,
        metric=cfg["metric"],
        min_training_years=int(cfg["minimum_training_years"]),
        week_window=int(cfg["seasonal_week_window"]),
        thresholds=[float(x) for x in cfg["robust_z_thresholds"]],
        future_window_weeks=int(cfg["future_window_weeks"]),
        event_quantile=float(cfg["event_quantile"]),
    )

    args.out_dir.mkdir(parents=True, exist_ok=True)
    result.summary.to_csv(args.out_dir / "anomaly_threshold_backtest.csv", index=False)
    result.predictions.to_csv(args.out_dir / "anomaly_backtest_predictions.csv", index=False)

    report = {
        "status": "experimental_internal_calibration",
        "metric": cfg["metric"],
        "rows": int(len(result.predictions)),
        "thresholds": cfg["robust_z_thresholds"],
        "event_definition": cfg["event_definition"],
        "validated_for_operational_alert": False,
    }
    (args.out_dir / "backtest_manifest.json").write_text(
        json.dumps(report, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
