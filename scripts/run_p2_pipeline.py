# -*- coding: utf-8 -*-
from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
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
from src.signal_confidence import build_signal_confidence
from src.silence_signals import build_silence_signals


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Executa o P2 experimental: baseline, tendência, anomalia, confiança e silêncio."
    )
    parser.add_argument(
        "--history",
        type=Path,
        default=ROOT / "data_candidate" / "history" / "municipal_weekly_history.csv",
    )
    parser.add_argument(
        "--current",
        type=Path,
        default=ROOT / "data_candidate" / "municipal_weekly_srag_mt_2026.csv",
    )
    parser.add_argument(
        "--quality",
        type=Path,
        default=ROOT / "data_candidate" / "quality_municipal_sivep_mt_2026.csv",
    )
    parser.add_argument(
        "--sivep-metadata",
        type=Path,
        default=ROOT / "data_candidate" / "sivep_mt_2026_metadata.json",
    )
    parser.add_argument(
        "--baseline-config",
        type=Path,
        default=ROOT / "config" / "baseline_v2.json",
    )
    parser.add_argument(
        "--confidence-config",
        type=Path,
        default=ROOT / "config" / "signal_confidence_v2.json",
    )
    parser.add_argument(
        "--out-dir",
        type=Path,
        default=ROOT / "data_candidate" / "signals",
    )
    parser.add_argument("--stable-week", type=int, default=None)
    parser.add_argument("--metric", default=None)
    args = parser.parse_args()

    for path in (args.history, args.current, args.quality, args.sivep_metadata):
        if not path.exists():
            raise FileNotFoundError(f"Artefato obrigatório ausente: {path}")

    baseline_cfg = json.loads(args.baseline_config.read_text(encoding="utf-8"))
    confidence_cfg = json.loads(args.confidence_config.read_text(encoding="utf-8"))
    sivep_meta = json.loads(args.sivep_metadata.read_text(encoding="utf-8"))

    stable_week = args.stable_week
    if stable_week is None:
        stable_week = sivep_meta.get("stable_week_provisional")
    if stable_week is None:
        raise ValueError("stable_week não informada e ausente no metadata SIVEP.")

    target_year = int(baseline_cfg["target_year"])
    metric = args.metric or baseline_cfg["primary_metric"]

    history = pd.read_csv(args.history, dtype={"codigo_ibge": "string"})
    current = pd.read_csv(args.current, dtype={"codigo_ibge": "string"})
    quality = pd.read_csv(args.quality, dtype={"codigo_ibge": "string"})
    if "ANO" not in current.columns:
        current["ANO"] = target_year

    baseline = build_seasonal_baseline(
        history,
        metric=metric,
        target_year=target_year,
        min_years=int(baseline_cfg["minimum_historical_years"]),
        week_window=int(baseline_cfg["seasonal_week_window"]),
        history_years=baseline_cfg.get("baseline_years_default"),
    )
    anomalies = add_anomaly_signal(
        current,
        baseline,
        metric=metric,
        stable_week=int(stable_week),
        robust_z_threshold=float(baseline_cfg["anomaly"]["robust_z_threshold"]),
    )
    trends = build_trend_signals(
        current,
        metric=metric,
        stable_week=int(stable_week),
        recent_weeks=int(baseline_cfg["trend"]["recent_weeks"]),
        previous_weeks=int(baseline_cfg["trend"]["previous_weeks"]),
        pseudocount=float(baseline_cfg["trend"]["pseudocount"]),
    )
    combined = combine_surveillance_signals(anomalies, trends)

    confidence = build_signal_confidence(
        combined,
        quality,
        stable_week=int(stable_week),
        thresholds=confidence_cfg["quality_thresholds"],
    )
    silence = build_silence_signals(
        current,
        baseline,
        confidence,
        stable_week=int(stable_week),
        metric=metric,
    )

    args.out_dir.mkdir(parents=True, exist_ok=True)
    outputs = {
        "baseline_seasonal.csv": baseline,
        "anomaly_signals.csv": anomalies,
        "trend_signals.csv": trends,
        "combined_signals.csv": combined,
        "signal_confidence.csv": confidence,
        "silence_signals.csv": silence,
    }
    for filename, frame in outputs.items():
        frame.to_csv(args.out_dir / filename, index=False, encoding="utf-8")

    manifest = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "model_status": "under_calibration",
        "validated_for_operational_alert": False,
        "target_year": target_year,
        "stable_week": int(stable_week),
        "metric": metric,
        "baseline_years": baseline_cfg.get("baseline_years_default"),
        "inputs": {
            "history": str(args.history),
            "current": str(args.current),
            "quality": str(args.quality),
            "sivep_metadata": str(args.sivep_metadata),
        },
        "outputs": {name: int(len(frame)) for name, frame in outputs.items()},
        "guards": {
            "historical_rate_denominator_guard": True,
            "quality_separate_from_risk": True,
            "silence_separate_from_risk": True,
            "composite_risk_score_enabled": False,
        },
    }
    manifest_path = args.out_dir / "p2_manifest.json"
    manifest_path.write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

    print(json.dumps(manifest, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
