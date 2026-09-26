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

from src.baseline_signals import (
    add_anomaly_signal,
    build_seasonal_baseline,
    build_trend_signals,
    combine_surveillance_signals,
)


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Constrói baseline sazonal, tendência e sinais experimentais SRAG-MT."
    )
    parser.add_argument("--history", type=Path, required=True)
    parser.add_argument("--current", type=Path, required=True)
    parser.add_argument("--stable-week", type=int, required=True)
    parser.add_argument("--metric", default=None)
    parser.add_argument("--config", type=Path, default=ROOT / "config" / "baseline_v2.json")
    parser.add_argument("--out-dir", type=Path, default=ROOT / "data_candidate" / "signals")
    args = parser.parse_args()

    cfg = json.loads(args.config.read_text(encoding="utf-8"))
    metric = args.metric or cfg["primary_metric"]
    history = pd.read_csv(args.history, dtype={"codigo_ibge": "string"})
    current = pd.read_csv(args.current, dtype={"codigo_ibge": "string"})
    if "ANO" not in current.columns:
        current["ANO"] = int(cfg["target_year"])

    baseline = build_seasonal_baseline(
        history,
        metric=metric,
        target_year=int(cfg["target_year"]),
        min_years=int(cfg["minimum_historical_years"]),
        week_window=int(cfg["seasonal_week_window"]),
        history_years=cfg.get("baseline_years_default"),
    )
    anomalies = add_anomaly_signal(
        current,
        baseline,
        metric=metric,
        stable_week=args.stable_week,
        robust_z_threshold=float(cfg["anomaly"]["robust_z_threshold"]),
    )
    trends = build_trend_signals(
        current,
        metric=metric,
        stable_week=args.stable_week,
        recent_weeks=int(cfg["trend"]["recent_weeks"]),
        previous_weeks=int(cfg["trend"]["previous_weeks"]),
        pseudocount=float(cfg["trend"]["pseudocount"]),
    )
    combined = combine_surveillance_signals(anomalies, trends)

    args.out_dir.mkdir(parents=True, exist_ok=True)
    baseline.to_csv(args.out_dir / "baseline_seasonal.csv", index=False)
    anomalies.to_csv(args.out_dir / "anomaly_signals.csv", index=False)
    trends.to_csv(args.out_dir / "trend_signals.csv", index=False)
    combined.to_csv(args.out_dir / "combined_signals.csv", index=False)

    print(f"baseline_rows={len(baseline)}")
    print(f"anomaly_rows={len(anomalies)}")
    print(f"trend_rows={len(trends)}")
    print(f"combined_rows={len(combined)}")
    print("model_status=under_calibration")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
