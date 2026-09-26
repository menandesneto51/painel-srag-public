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

from src.historical_baseline import (
    build_municipal_weekly,
    robust_municipal_weekly_baseline,
)


def parse_years(value: str) -> list[int]:
    years = sorted({int(x.strip()) for x in value.split(",") if x.strip()})
    if not years:
        raise ValueError("Informe ao menos um ano.")
    return years


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Constrói histórico municipal por contagem com validade territorial explícita."
    )
    parser.add_argument(
        "--sources",
        type=Path,
        default=ROOT / "config" / "historical_sources.json",
    )
    parser.add_argument(
        "--raw-dir",
        type=Path,
        default=ROOT / "data_raw" / "historical",
    )
    parser.add_argument(
        "--population-reference",
        type=Path,
        default=ROOT / "reference" / "population_mt_2026.csv",
    )
    parser.add_argument(
        "--harmonization",
        type=Path,
        default=ROOT / "config" / "municipality_harmonization.json",
    )
    parser.add_argument("--years", default="2019,2020,2021,2022,2023,2024,2025")
    parser.add_argument(
        "--baseline-years",
        required=True,
        help="Seleção explícita, ex.: 2023,2024,2025",
    )
    parser.add_argument("--metric", default="casos")
    parser.add_argument(
        "--out-dir",
        type=Path,
        default=ROOT / "data_candidate" / "p2",
    )
    args = parser.parse_args()

    config = json.loads(args.sources.read_text(encoding="utf-8"))
    years = parse_years(args.years)
    baseline_years = parse_years(args.baseline_years)

    all_municipal = []
    per_year = {}
    for year in years:
        source = config["sources"].get(str(year))
        if not source:
            raise ValueError(f"Ano {year} não configurado.")
        path = args.raw_dir / source["local_filename"]
        if not path.exists():
            raise FileNotFoundError(
                f"{path}. Execute scripts/download_historical_sources.py --years {year}"
            )

        municipal, meta = build_municipal_weekly(
            path,
            year,
            args.population_reference,
            args.harmonization,
        )
        all_municipal.append(municipal)
        per_year[str(year)] = meta

    historical = pd.concat(all_municipal, ignore_index=True)
    baseline = robust_municipal_weekly_baseline(
        historical,
        args.metric,
        baseline_years,
    )

    args.out_dir.mkdir(parents=True, exist_ok=True)
    historical_path = args.out_dir / "historical_weekly_municipal_mt.csv"
    baseline_path = args.out_dir / f"baseline_{args.metric}_municipal_mt.csv"
    meta_path = args.out_dir / "historical_municipal_metadata.json"

    historical.to_csv(historical_path, index=False)
    baseline.to_csv(baseline_path, index=False)
    meta_path.write_text(
        json.dumps({
            "years_processed": years,
            "baseline_years": baseline_years,
            "metric": args.metric,
            "per_year": per_year,
            "rates_calculated": False,
            "zero_fill_policy": "only_when_municipality_valid",
            "predecessor_reconstruction_enabled": False,
        }, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )

    print(f"historical_rows={len(historical)}")
    print(f"baseline_rows={len(baseline)}")
    print(f"historical={historical_path}")
    print(f"baseline={baseline_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
