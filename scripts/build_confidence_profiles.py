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

from src.confidence import build_confidence_profile, load_confidence_config


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Constrói perfis transparentes de confiança do sinal SRAG."
    )
    parser.add_argument("--quality", type=Path, required=True)
    parser.add_argument("--stable", action="store_true")
    parser.add_argument("--lab-coverage", type=float, default=None)
    parser.add_argument("--vintage-count", type=int, default=None)
    parser.add_argument("--baseline-years", type=int, default=None)
    parser.add_argument(
        "--config",
        type=Path,
        default=ROOT / "config" / "confidence_v2.json",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=ROOT / "data_candidate" / "p2" / "confidence_municipal.csv",
    )
    args = parser.parse_args()

    cfg = load_confidence_config(args.config)
    quality = pd.read_csv(args.quality)

    required = {
        "codigo_ibge",
        "municipio",
        "registros",
        "atraso_notificacao_mediana_dias",
        "desfecho_completo_percent",
        "inconsistencia_temporal_percent",
    }
    missing = required.difference(quality.columns)
    if missing:
        raise ValueError(
            "Arquivo de qualidade sem colunas: " + ", ".join(sorted(missing))
        )

    rows = []
    for row in quality.itertuples(index=False):
        profile = build_confidence_profile(
            config=cfg,
            is_stable=args.stable,
            volume=row.registros,
            outcome_completeness_percent=row.desfecho_completo_percent,
            notification_delay_median_days=row.atraso_notificacao_mediana_dias,
            temporal_inconsistency_percent=row.inconsistencia_temporal_percent,
            laboratory_coverage_percent=args.lab_coverage,
            vintage_count=args.vintage_count,
            baseline_year_count=args.baseline_years,
        )
        rows.append({
            "codigo_ibge": row.codigo_ibge,
            "municipio": row.municipio,
            "confidence_class": profile["confidence_class"],
            "reporting_quality_class": profile["reporting_quality_class"],
            "limiting_dimensions": ",".join(profile["limiting_dimensions"]),
            "stability_class": profile["components"]["stability"],
            "volume_class": profile["components"]["volume"],
            "outcome_completeness_class": profile["components"]["outcome_completeness"],
            "timeliness_class": profile["components"]["timeliness"],
            "temporal_consistency_class": profile["components"]["temporal_consistency"],
            "laboratory_coverage_class": profile["components"]["laboratory_coverage"],
            "vintage_depth_class": profile["components"]["vintage_depth"],
            "baseline_depth_class": profile["components"]["baseline_depth"],
            "model_status": profile["model_status"],
        })

    output = pd.DataFrame(rows)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    output.to_csv(args.output, index=False)

    metadata = {
        "model_id": cfg["model_id"],
        "version": cfg["version"],
        "status": cfg["status"],
        "overall_rule": cfg["overall_rule"],
        "numeric_score_enabled": cfg["numeric_score_enabled"],
        "rows": len(output),
        "stable_flag": args.stable,
    }
    args.output.with_suffix(".json").write_text(
        json.dumps(metadata, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    print(json.dumps(metadata, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
