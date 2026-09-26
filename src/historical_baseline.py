# -*- coding: utf-8 -*-
from __future__ import annotations

from pathlib import Path

import pandas as pd

from src.epi_calendar import epidemiological_week_start
from src.sivep_pipeline import detect_text_format, normalize_week


BASIC_FIELDS = {
    "uf": "SG_UF",
    "week": "SEM_PRI",
    "hospital": "HOSPITAL",
    "icu": "UTI",
    "outcome": "EVOLUCAO",
}


def build_state_weekly(
    sivep_path: Path,
    year: int,
    residence_uf: str = "MT",
    chunksize: int = 100_000,
) -> tuple[pd.DataFrame, dict]:
    encoding, sep = detect_text_format(sivep_path)
    required = list(BASIC_FIELDS.values())
    header = pd.read_csv(sivep_path, sep=sep, encoding=encoding, nrows=0)
    missing = [field for field in required if field not in header.columns]
    if missing:
        raise ValueError(f"Banco SIVEP {year} sem campos básicos: {missing}")

    parts: list[pd.DataFrame] = []
    source_rows = 0
    mt_rows = 0
    invalid_week_rows = 0

    reader = pd.read_csv(
        sivep_path,
        sep=sep,
        encoding=encoding,
        dtype="string",
        usecols=required,
        chunksize=chunksize,
        low_memory=False,
    )
    try:
        for chunk in reader:
            source_rows += len(chunk)
            uf = chunk[BASIC_FIELDS["uf"]].astype("string").str.strip().str.upper()
            chunk = chunk.loc[uf == residence_uf].copy()
            mt_rows += len(chunk)
            if chunk.empty:
                continue

            chunk["SE"] = chunk[BASIC_FIELDS["week"]].map(
                lambda value: normalize_week(value, year)
            )
            invalid_week_rows += int(chunk["SE"].isna().sum())
            chunk = chunk.dropna(subset=["SE"]).copy()
            if chunk.empty:
                continue

            chunk["hospitalizado"] = (
                chunk[BASIC_FIELDS["hospital"]].astype("string").str.strip().eq("1").astype(int)
            )
            chunk["uti"] = (
                chunk[BASIC_FIELDS["icu"]].astype("string").str.strip().eq("1").astype(int)
            )
            outcome = chunk[BASIC_FIELDS["outcome"]].astype("string").str.strip()
            chunk["obito"] = outcome.eq("2").astype(int)
            chunk["cura"] = outcome.eq("1").astype(int)

            part = (
                chunk.groupby("SE", as_index=False)
                .agg(
                    casos=("SE", "size"),
                    hospitalizacoes=("hospitalizado", "sum"),
                    uti=("uti", "sum"),
                    obitos=("obito", "sum"),
                    curas=("cura", "sum"),
                )
            )
            parts.append(part)
    finally:
        reader.close()

    if parts:
        weekly = pd.concat(parts, ignore_index=True)
        weekly = (
            weekly.groupby("SE", as_index=False)[
                ["casos", "hospitalizacoes", "uti", "obitos", "curas"]
            ]
            .sum()
            .sort_values("SE")
        )
        max_week = int(weekly["SE"].max())
        skeleton = pd.DataFrame({"SE": range(1, max_week + 1)})
        weekly = skeleton.merge(weekly, on="SE", how="left")
        for field in ("casos", "hospitalizacoes", "uti", "obitos", "curas"):
            weekly[field] = weekly[field].fillna(0).astype(int)
    else:
        max_week = None
        weekly = pd.DataFrame(
            columns=["SE", "casos", "hospitalizacoes", "uti", "obitos", "curas"]
        )

    weekly["ano"] = int(year)
    weekly["semana_inicio"] = weekly["SE"].map(
        lambda week: epidemiological_week_start(year, int(week)).isoformat()
    )
    weekly = weekly[
        ["ano", "SE", "semana_inicio", "casos", "hospitalizacoes", "uti", "obitos", "curas"]
    ]

    metadata = {
        "year": int(year),
        "territorial_scope": "residence_uf_MT",
        "source_rows": int(source_rows),
        "mt_rows": int(mt_rows),
        "invalid_week_rows": int(invalid_week_rows),
        "max_observed_week": max_week,
        "population_denominator_used": False,
        "municipal_filter_used": False,
    }
    return weekly, metadata


def robust_weekly_baseline(
    historical: pd.DataFrame,
    metric: str,
    baseline_years: list[int],
) -> pd.DataFrame:
    years = sorted({int(year) for year in baseline_years})
    if len(years) < 3:
        raise ValueError("Baseline robusto exige pelo menos 3 anos explicitamente selecionados.")
    if metric not in historical.columns:
        raise ValueError(f"Métrica ausente: {metric}")

    work = historical.loc[historical["ano"].isin(years), ["ano", "SE", metric]].copy()
    if work.empty:
        raise ValueError("Nenhuma observação para os anos de baseline selecionados.")

    work[metric] = pd.to_numeric(work[metric], errors="coerce")
    work = work.dropna(subset=[metric])

    rows = []
    for week, sub in work.groupby("SE"):
        values = sub[metric].astype(float)
        median = float(values.median())
        abs_dev = (values - median).abs()
        rows.append({
            "SE": int(week),
            "metric": metric,
            "baseline_years": ",".join(map(str, years)),
            "n_years": int(sub["ano"].nunique()),
            "median": median,
            "q25": float(values.quantile(0.25)),
            "q75": float(values.quantile(0.75)),
            "mad": float(abs_dev.median()),
            "min": float(values.min()),
            "max": float(values.max()),
        })
    return pd.DataFrame(rows).sort_values("SE").reset_index(drop=True)
