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

from src.silence import classify_silence, load_silence_config


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Classifica candidatos a silêncio epidemiológico sem tratar zero como silêncio automático."
    )
    parser.add_argument("--input", type=Path, required=True)
    parser.add_argument(
        "--config",
        type=Path,
        default=ROOT / "config" / "silence_v2.json",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=ROOT / "data_candidate" / "p2" / "silence_candidates.csv",
    )
    args = parser.parse_args()

    cfg = load_silence_config(args.config)
    data = pd.read_csv(args.input)
    required = {
        "codigo_ibge",
        "municipio",
        "observed_cases",
        "baseline_median",
        "baseline_q75",
        "baseline_n_years",
        "reporting_evidence",
        "data_quality_class",
        "regional_signal_status",
    }
    missing = required.difference(data.columns)
    if missing:
        raise ValueError("Entrada sem colunas: " + ", ".join(sorted(missing)))

    rows = []
    for row in data.itertuples(index=False):
        result = classify_silence(
            observed_cases=int(row.observed_cases),
            baseline_median=None if pd.isna(row.baseline_median) else float(row.baseline_median),
            baseline_q75=None if pd.isna(row.baseline_q75) else float(row.baseline_q75),
            baseline_n_years=int(row.baseline_n_years),
            reporting_evidence=str(row.reporting_evidence),
            data_quality_class=None if pd.isna(row.data_quality_class) else str(row.data_quality_class),
            regional_signal_status=None if pd.isna(row.regional_signal_status) else str(row.regional_signal_status),
            min_baseline_years=int(cfg["min_baseline_years"]),
            priority_expected_median=float(cfg["priority_expected_median"]),
            regional_priority_signals=set(cfg["regional_priority_signals"]),
        )
        rows.append({
            "codigo_ibge": row.codigo_ibge,
            "municipio": row.municipio,
            "observed_cases": row.observed_cases,
            "baseline_median": row.baseline_median,
            "reporting_evidence": row.reporting_evidence,
            "data_quality_class": row.data_quality_class,
            "regional_signal_status": row.regional_signal_status,
            **result,
        })

    output = pd.DataFrame(rows)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    output.to_csv(args.output, index=False)
    metadata = {
        "model_id": cfg["model_id"],
        "version": cfg["version"],
        "status": cfg["status"],
        "rows": len(output),
        "priority_candidates": int(output["priority_candidate"].sum()) if not output.empty else 0,
    }
    args.output.with_suffix(".json").write_text(
        json.dumps(metadata, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    print(json.dumps(metadata, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
