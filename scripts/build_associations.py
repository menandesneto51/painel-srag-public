# -*- coding: utf-8 -*-
from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.associations import build_crude_associations


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Recalcula OR brutas reproduzíveis para UTI e óbito."
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
    parser.add_argument("--out-dir", type=Path, default=ROOT / "data_candidate")
    args = parser.parse_args()

    outputs = build_crude_associations(args.sivep, args.population, args.config)
    args.out_dir.mkdir(parents=True, exist_ok=True)
    for outcome, table in outputs.items():
        path = args.out_dir / f"or_{outcome}_crude_v2.csv"
        table.to_csv(path, index=False, encoding="utf-8")
        print(f"{outcome}={path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
