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

from src.signal_confidence import build_signal_confidence
from src.silence_signals import build_silence_signals


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Constrói confiança do sinal e silêncio epidemiológico experimental."
    )
    parser.add_argument("--combined-signals", type=Path, required=True)
    parser.add_argument("--baseline", type=Path, required=True)
    parser.add_argument("--current", type=Path, required=True)
    parser.add_argument("--quality", type=Path, required=True)
    parser.add_argument("--stable-week", type=int, required=True)
    parser.add_argument("--metric", default="hospitalizacoes")
    parser.add_argument(
        "--config",
        type=Path,
        default=ROOT / "config" / "signal_confidence_v2.json",
    )
    parser.add_argument(
        "--out-dir",
        type=Path,
        default=ROOT / "data_candidate" / "signals",
    )
    args = parser.parse_args()

    cfg = json.loads(args.config.read_text(encoding="utf-8"))
    combined = pd.read_csv(args.combined_signals, dtype={"codigo_ibge": "string"})
    baseline = pd.read_csv(args.baseline, dtype={"codigo_ibge": "string"})
    current = pd.read_csv(args.current, dtype={"codigo_ibge": "string"})
    quality = pd.read_csv(args.quality, dtype={"codigo_ibge": "string"})

    confidence = build_signal_confidence(
        combined,
        quality,
        stable_week=args.stable_week,
        thresholds=cfg["quality_thresholds"],
    )
    silence = build_silence_signals(
        current,
        baseline,
        confidence,
        stable_week=args.stable_week,
        metric=args.metric,
    )

    args.out_dir.mkdir(parents=True, exist_ok=True)
    confidence_path = args.out_dir / "signal_confidence.csv"
    silence_path = args.out_dir / "silence_signals.csv"
    confidence.to_csv(confidence_path, index=False, encoding="utf-8")
    silence.to_csv(silence_path, index=False, encoding="utf-8")

    print(f"confidence_rows={len(confidence)}")
    print(f"silence_rows={len(silence)}")
    print("confidence_model_status=under_calibration")
    print("silence_model_status=under_calibration")
    print("validated_for_operational_alert=false")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
