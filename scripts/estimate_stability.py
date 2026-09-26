# -*- coding: utf-8 -*-
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.stability import estimate_delay_based_stability


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Estima lag provisório de estabilidade a partir dos atrasos do SIVEP."
    )
    parser.add_argument(
        "--sivep",
        type=Path,
        default=ROOT / "data_raw" / "sivep_gripe_2026_2026-09-14.csv",
    )
    parser.add_argument(
        "--population",
        type=Path,
        default=ROOT / "reference" / "population_mt_2026.csv",
    )
    parser.add_argument(
        "--config",
        type=Path,
        default=ROOT / "config" / "sivep_2026_schema.json",
    )
    parser.add_argument("--quantile", type=float, default=0.95)
    parser.add_argument(
        "--output",
        type=Path,
        default=ROOT / "data_candidate" / "stability_delay_estimate.json",
    )
    args = parser.parse_args()

    if not 0.5 <= args.quantile < 1.0:
        raise ValueError("--quantile deve estar entre 0.5 e <1.0")

    result = estimate_delay_based_stability(
        args.sivep, args.population, args.config, quantile=args.quantile
    )
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(
        json.dumps(result, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
