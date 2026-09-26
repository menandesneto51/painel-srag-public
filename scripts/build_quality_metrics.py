# -*- coding: utf-8 -*-
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.quality_metrics import build_quality_metrics


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Gera indicadores municipais de qualidade/oportunidade do SIVEP-Gripe."
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
    parser.add_argument(
        "--out-dir",
        type=Path,
        default=ROOT / "data_candidate",
    )
    args = parser.parse_args()

    if not args.sivep.exists():
        raise FileNotFoundError(
            f"Banco SIVEP não encontrado em {args.sivep}. "
            "Execute scripts/download_official_sources.py primeiro."
        )

    municipal, metadata = build_quality_metrics(
        args.sivep, args.population, args.config
    )
    args.out_dir.mkdir(parents=True, exist_ok=True)

    csv_path = args.out_dir / "quality_municipal_sivep_mt_2026.csv"
    meta_path = args.out_dir / "quality_metadata.json"
    municipal.to_csv(csv_path, index=False, encoding="utf-8")
    meta_path.write_text(
        json.dumps(metadata, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

    print(json.dumps(metadata, ensure_ascii=False, indent=2))
    print(f"quality={csv_path}")
    print(f"metadata={meta_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
