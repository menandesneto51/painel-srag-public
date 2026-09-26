# -*- coding: utf-8 -*-
from __future__ import annotations

import argparse
import json
import sys
import tempfile
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.epi_calendar import epidemiological_weeks_in_year
from src.sivep_pipeline import build_mt_aggregates

DEFAULT_SOURCES = ROOT / "config" / "sivep_history_sources.json"
DEFAULT_SCHEMA = ROOT / "config" / "sivep_2026_schema.json"
DEFAULT_POPULATION = ROOT / "reference" / "population_mt_2026.csv"
DEFAULT_RAW = ROOT / "data_raw" / "sivep_history"
DEFAULT_OUT = ROOT / "data_candidate" / "history" / "municipal_weekly_history.csv"


def make_year_config(base_schema: dict, year: int, destination: Path) -> Path:
    cfg = json.loads(json.dumps(base_schema))
    cfg["reference_year"] = int(year)
    destination.write_text(json.dumps(cfg, ensure_ascii=False, indent=2), encoding="utf-8")
    return destination


def densify_full_year(
    municipal_weekly: pd.DataFrame,
    population: pd.DataFrame,
    year: int,
) -> pd.DataFrame:
    weeks = epidemiological_weeks_in_year(year)
    base = population[["codigo_ibge", "municipio", "populacao"]].copy()
    base["codigo_ibge"] = base["codigo_ibge"].astype("string").str.zfill(7)
    base["_join"] = 1
    week_df = pd.DataFrame({"SE": range(1, weeks + 1), "_join": 1})
    panel = base.merge(week_df, on="_join", how="inner").drop(columns="_join")

    observed_cols = [
        "codigo_ibge",
        "SE",
        "casos",
        "hospitalizacoes",
        "uti",
        "obitos",
        "curas",
    ]
    observed = municipal_weekly[observed_cols].copy() if not municipal_weekly.empty else pd.DataFrame(columns=observed_cols)
    panel = panel.merge(observed, on=["codigo_ibge", "SE"], how="left", validate="one_to_one")

    for col in ("casos", "hospitalizacoes", "uti", "obitos", "curas"):
        panel[col] = pd.to_numeric(panel[col], errors="coerce").fillna(0).astype(int)

    panel["ANO"] = int(year)
    panel["incidencia_srag_100k"] = panel["casos"] / panel["populacao"] * 100000.0
    panel["hospitalizacao_100k"] = panel["hospitalizacoes"] / panel["populacao"] * 100000.0
    panel["uti_100k"] = panel["uti"] / panel["populacao"] * 100000.0
    panel["obito_100k"] = panel["obitos"] / panel["populacao"] * 100000.0

    expected = 142 * weeks
    if len(panel) != expected:
        raise ValueError(f"{year}: painel incompleto: {len(panel)} linhas; esperado {expected}.")
    if panel.duplicated(["ANO", "SE", "codigo_ibge"]).any():
        raise ValueError(f"{year}: duplicidade em ANO+SE+codigo_ibge.")
    return panel


def main() -> int:
    parser = argparse.ArgumentParser(description="Constrói painel histórico municipal x SE para baseline SRAG.")
    parser.add_argument("--sources", type=Path, default=DEFAULT_SOURCES)
    parser.add_argument("--schema", type=Path, default=DEFAULT_SCHEMA)
    parser.add_argument("--population", type=Path, default=DEFAULT_POPULATION)
    parser.add_argument("--raw-dir", type=Path, default=DEFAULT_RAW)
    parser.add_argument("--out", type=Path, default=DEFAULT_OUT)
    parser.add_argument("--years", nargs="*", type=int, default=None)
    args = parser.parse_args()

    sources = json.loads(args.sources.read_text(encoding="utf-8"))["history"]
    base_schema = json.loads(args.schema.read_text(encoding="utf-8"))
    population = pd.read_csv(args.population, dtype={"codigo_ibge": "string"})

    years = sorted(int(y) for y in sources)
    if args.years:
        years = sorted(args.years)

    panels = []
    metadata = {"years": {}, "population_reference": str(args.population)}
    with tempfile.TemporaryDirectory(prefix="srag-history-config-") as tmp:
        tmpdir = Path(tmp)
        for year in years:
            source = sources.get(str(year))
            if source is None:
                raise ValueError(f"Ano {year} não configurado.")
            path = args.raw_dir / source["local_filename"]
            if not path.exists():
                raise FileNotFoundError(
                    f"{year}: arquivo não encontrado em {path}. "
                    "Execute scripts/download_sivep_history.py antes."
                )

            cfg_path = make_year_config(base_schema, year, tmpdir / f"sivep_{year}.json")
            _, _, municipal_weekly, meta = build_mt_aggregates(
                path,
                args.population,
                cfg_path,
            )
            panel = densify_full_year(municipal_weekly, population, year)
            panels.append(panel)
            metadata["years"][str(year)] = {
                "source": source,
                "source_rows": meta["source_rows"],
                "mt_residence_rows": meta["mt_residence_rows"],
                "max_observed_week": meta["max_observed_week"],
                "expected_epi_weeks": epidemiological_weeks_in_year(year),
                "panel_rows": len(panel),
            }
            print(f"[OK] {year}: {len(panel)} linhas")

    history = pd.concat(panels, ignore_index=True)
    history = history.sort_values(["ANO", "SE", "codigo_ibge"]).reset_index(drop=True)

    args.out.parent.mkdir(parents=True, exist_ok=True)
    history.to_csv(args.out, index=False, encoding="utf-8")
    meta_path = args.out.with_suffix(".metadata.json")
    meta_path.write_text(json.dumps(metadata, ensure_ascii=False, indent=2), encoding="utf-8")

    print(f"history_rows={len(history)}")
    print(f"output={args.out}")
    print(f"metadata={meta_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
