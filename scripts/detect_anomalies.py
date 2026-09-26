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

from src.anomaly_detection import detect_robust_anomalies, load_anomaly_config


def main() -> int:
    parser = argparse.ArgumentParser(description="Detecta sinais experimentais contra baseline robusto.")
    parser.add_argument("--observed", type=Path, required=True)
    parser.add_argument("--baseline", type=Path, required=True)
    parser.add_argument("--metric", default="casos")
    parser.add_argument("--stable-week", type=int, required=True)
    parser.add_argument(
        "--config",
        type=Path,
        default=ROOT / "config" / "anomaly_v2.json",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=ROOT / "data_candidate" / "p2" / "anomaly_state_mt.csv",
    )
    args = parser.parse_args()

    cfg = load_anomaly_config(args.config)
    observed = pd.read_csv(args.observed)
    baseline = pd.read_csv(args.baseline)

    result = detect_robust_anomalies(
        observed,
        baseline,
        metric=args.metric,
        stable_week=args.stable_week,
        z_threshold=float(cfg["z_threshold"]),
        persistence_weeks=int(cfg["persistence_weeks"]),
        min_baseline_years=int(cfg["min_baseline_years"]),
    )
    args.output.parent.mkdir(parents=True, exist_ok=True)
    result.to_csv(args.output, index=False)

    metadata = {
        "model_id": cfg["model_id"],
        "version": cfg["version"],
        "status": cfg["status"],
        "metric": args.metric,
        "stable_week": args.stable_week,
        "rows": len(result),
        "persistent_elevated_weeks": int(result["persistent_elevated"].sum()) if not result.empty else 0,
    }
    meta_path = args.output.with_suffix(".json")
    meta_path.write_text(
        json.dumps(metadata, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    print(json.dumps(metadata, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
