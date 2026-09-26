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

from src.historical_baseline import build_state_weekly, robust_weekly_baseline


def parse_years(value: str) -> list[int]:
    years = sorted({int(x.strip()) for x in value.split(",") if x.strip()})
    if not years:
        raise ValueError("Informe ao menos um ano.")
    return years


def main() -> int:
    parser = argparse.ArgumentParser(description="Constrói histórico semanal estadual e baseline robusto.")
    parser.add_argument("--sources", type=Path, default=ROOT / "config" / "historical_sources.json")
    parser.add_argument("--raw-dir", type=Path, default=ROOT / "data_raw" / "historical")
    parser.add_argument("--years", default="2019,2020,2021,2022,2023,2024,2025")
    parser.add_argument("--baseline-years", required=True, help="Seleção explícita, ex.: 2023,2024,2025")
    parser.add_argument("--metric", default="casos")
    parser.add_argument("--out-dir", type=Path, default=ROOT / "data_candidate" / "p2")
    args = parser.parse_args()

    config = json.loads(args.sources.read_text(encoding="utf-8"))
    years = parse_years(args.years)
    baseline_years = parse_years(args.baseline_years)

    all_weekly = []
    metadata = {}
    for year in years:
        source = config["sources"].get(str(year))
        if not source:
            raise ValueError(f"Ano {year} não configurado.")
        path = args.raw_dir / source["local_filename"]
        if not path.exists():
            raise FileNotFoundError(
                f"{path}. Execute scripts/download_historical_sources.py --years {year}"
            )
        weekly, meta = build_state_weekly(path, year)
        all_weekly.append(weekly)
        metadata[str(year)] = meta

    historical = pd.concat(all_weekly, ignore_index=True)
    baseline = robust_weekly_baseline(historical, args.metric, baseline_years)

    args.out_dir.mkdir(parents=True, exist_ok=True)
    historical.to_csv(args.out_dir / "historical_weekly_state_mt.csv", index=False)
    baseline.to_csv(args.out_dir / f"baseline_{args.metric}_state_mt.csv", index=False)
    (args.out_dir / "historical_metadata.json").write_text(
        json.dumps({
            "years_processed": years,
            "baseline_years": baseline_years,
            "metric": args.metric,
            "per_year": metadata,
            "comparability_note": config.get("comparability_note"),
        }, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    print(f"historical_rows={len(historical)}")
    print(f"baseline_rows={len(baseline)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
