# -*- coding: utf-8 -*-
from __future__ import annotations

import argparse
import hashlib
import json
import shutil
from datetime import date
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Captura um vintage agregado semanal do SIVEP para backtesting."
    )
    parser.add_argument(
        "--weekly",
        type=Path,
        default=ROOT / "data_candidate" / "weekly_srag_mt_2026.csv",
    )
    parser.add_argument(
        "--pipeline-metadata",
        type=Path,
        default=ROOT / "data_candidate" / "sivep_mt_2026_metadata.json",
    )
    parser.add_argument(
        "--sources",
        type=Path,
        default=ROOT / "config" / "sources.json",
    )
    parser.add_argument("--vintage-date", default=None)
    parser.add_argument(
        "--out-root",
        type=Path,
        default=ROOT / "vintages" / "sivep",
    )
    parser.add_argument("--force", action="store_true")
    args = parser.parse_args()

    if not args.weekly.exists():
        raise FileNotFoundError(f"Agregado semanal não encontrado: {args.weekly}")

    weekly = pd.read_csv(args.weekly)
    required = {"SE", "casos", "hospitalizacoes", "uti", "obitos", "curas"}
    missing = required.difference(weekly.columns)
    if missing:
        raise ValueError(f"Agregado semanal sem colunas: {sorted(missing)}")

    sources = json.loads(args.sources.read_text(encoding="utf-8"))
    source = sources["sources"]["sivep_gripe_2026"]
    vintage_date = args.vintage_date or source["resource_date"]
    date.fromisoformat(vintage_date)

    destination = args.out_root / vintage_date
    if destination.exists() and any(destination.iterdir()) and not args.force:
        raise FileExistsError(
            f"Vintage {vintage_date} já existe. Use --force apenas se a origem for a mesma."
        )
    destination.mkdir(parents=True, exist_ok=True)

    weekly_out = destination / "weekly.csv"
    weekly.sort_values("SE").to_csv(weekly_out, index=False, encoding="utf-8")

    pipeline_metadata = {}
    if args.pipeline_metadata.exists():
        pipeline_metadata = json.loads(
            args.pipeline_metadata.read_text(encoding="utf-8")
        )

    metadata = {
        "vintage_date": vintage_date,
        "reference_year": int(pipeline_metadata.get("reference_year", 2026)),
        "source_resource_date": source["resource_date"],
        "source_resource_id": source.get("resource_id"),
        "source_url": source["url"],
        "weekly_sha256": sha256(weekly_out),
        "row_count": int(len(weekly)),
        "max_observed_week": (
            int(pd.to_numeric(weekly["SE"], errors="coerce").max())
            if not weekly.empty
            else None
        ),
        "pipeline_metadata": pipeline_metadata,
        "contains_microdata": False,
    }
    (destination / "metadata.json").write_text(
        json.dumps(metadata, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )

    print(f"Vintage capturado: {destination}")
    print(json.dumps(metadata, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
