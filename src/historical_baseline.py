# -*- coding: utf-8 -*-
from __future__ import annotations

from pathlib import Path

import pandas as pd

from src.epi_calendar import epidemiological_week_start
from src.sivep_pipeline import detect_text_format, digits, municipality_reference, normalize_week


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



def load_municipality_harmonization(path: Path) -> dict:
    import json
    return json.loads(path.read_text(encoding="utf-8"))


def municipality_valid_from_year(
    codigo_ibge: str,
    harmonization: dict,
) -> int:
    exceptions = harmonization.get("exceptions", {})
    specific = exceptions.get(str(codigo_ibge), {})
    return int(
        specific.get(
            "valid_from_year",
            harmonization.get("default_valid_from_year", 2019),
        )
    )


def build_municipal_weekly(
    sivep_path: Path,
    year: int,
    population_reference_path: Path,
    harmonization_path: Path,
    residence_uf: str = "MT",
    chunksize: int = 100_000,
) -> tuple[pd.DataFrame, dict]:
    encoding, sep = detect_text_format(sivep_path)
    required = ["SG_UF", "CO_MUN_RES", "SEM_PRI"]
    header = pd.read_csv(sivep_path, sep=sep, encoding=encoding, nrows=0)
    missing = [field for field in required if field not in header.columns]
    if missing:
        raise ValueError(f"Banco SIVEP {year} sem campos municipais: {missing}")

    ref = municipality_reference(population_reference_path)
    harmonization = load_municipality_harmonization(harmonization_path)
    ref = ref.copy()
    ref["valid_from_year"] = ref["codigo_ibge"].map(
        lambda code: municipality_valid_from_year(str(code), harmonization)
    )
    valid_ref = ref.loc[ref["valid_from_year"] <= int(year)].copy()
    valid_codes = set(valid_ref["codigo_sivep_6"].tolist())

    parts: list[pd.DataFrame] = []
    mt_rows = 0
    invalid_or_unmapped_rows = 0
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
            uf = chunk["SG_UF"].astype("string").str.strip().str.upper()
            chunk = chunk.loc[uf == residence_uf].copy()
            mt_rows += len(chunk)
            if chunk.empty:
                continue

            chunk["codigo_sivep_6"] = chunk["CO_MUN_RES"].map(digits).str[:6]
            valid_code = chunk["codigo_sivep_6"].isin(valid_codes)
            invalid_or_unmapped_rows += int((~valid_code).sum())
            chunk = chunk.loc[valid_code].copy()
            if chunk.empty:
                continue

            chunk["SE"] = chunk["SEM_PRI"].map(
                lambda value: normalize_week(value, int(year))
            )
            invalid_week_rows += int(chunk["SE"].isna().sum())
            chunk = chunk.dropna(subset=["SE"]).copy()
            if chunk.empty:
                continue

            part = (
                chunk.groupby(["codigo_sivep_6", "SE"], as_index=False)
                .size()
                .rename(columns={"size": "casos"})
            )
            parts.append(part)
    finally:
        reader.close()

    if parts:
        counts = pd.concat(parts, ignore_index=True)
        counts = (
            counts.groupby(["codigo_sivep_6", "SE"], as_index=False)["casos"]
            .sum()
        )
        max_week = int(counts["SE"].max())
    else:
        counts = pd.DataFrame(columns=["codigo_sivep_6", "SE", "casos"])
        max_week = 52

    # Zero-fill somente para municípios válidos no ano.
    skeleton = pd.MultiIndex.from_product(
        [valid_ref["codigo_sivep_6"].tolist(), range(1, max_week + 1)],
        names=["codigo_sivep_6", "SE"],
    ).to_frame(index=False)

    municipal = skeleton.merge(
        counts,
        on=["codigo_sivep_6", "SE"],
        how="left",
        validate="one_to_one",
    )
    municipal["casos"] = municipal["casos"].fillna(0).astype(int)

    lookup = valid_ref.set_index("codigo_sivep_6")
    municipal["codigo_ibge"] = municipal["codigo_sivep_6"].map(
        lookup["codigo_ibge"]
    )
    municipal["municipio"] = municipal["codigo_sivep_6"].map(
        lookup["municipio"]
    )
    municipal["ano"] = int(year)
    municipal["territorial_valid_from_year"] = municipal["codigo_sivep_6"].map(
        lookup["valid_from_year"]
    )
    municipal["zero_fill_authorized"] = True

    municipal = municipal[[
        "ano",
        "SE",
        "codigo_ibge",
        "codigo_sivep_6",
        "municipio",
        "territorial_valid_from_year",
        "zero_fill_authorized",
        "casos",
    ]].sort_values(["codigo_ibge", "SE"]).reset_index(drop=True)

    if municipal.duplicated(["ano", "SE", "codigo_ibge"]).any():
        raise ValueError("Matriz municipal histórica contém chave duplicada.")

    metadata = {
        "year": int(year),
        "municipalities_valid_in_year": int(valid_ref["codigo_ibge"].nunique()),
        "max_observed_week": int(max_week),
        "mt_rows_seen": int(mt_rows),
        "invalid_or_unmapped_rows": int(invalid_or_unmapped_rows),
        "invalid_week_rows": int(invalid_week_rows),
        "zero_fill_policy": "only_valid_municipalities",
        "rates_calculated": False,
    }
    return municipal, metadata


def robust_municipal_weekly_baseline(
    historical_municipal: pd.DataFrame,
    metric: str,
    baseline_years: list[int],
) -> pd.DataFrame:
    years = sorted({int(year) for year in baseline_years})
    if len(years) < 3:
        raise ValueError("Baseline municipal exige pelo menos 3 anos selecionados.")

    required = {
        "ano",
        "SE",
        "codigo_ibge",
        "municipio",
        "zero_fill_authorized",
        metric,
    }
    missing = required.difference(historical_municipal.columns)
    if missing:
        raise ValueError(
            "Histórico municipal sem colunas: " + ", ".join(sorted(missing))
        )

    work = historical_municipal.loc[
        historical_municipal["ano"].isin(years)
        & historical_municipal["zero_fill_authorized"].astype(bool)
    ].copy()
    work[metric] = pd.to_numeric(work[metric], errors="coerce")
    work = work.dropna(subset=[metric])

    rows = []
    group_cols = ["codigo_ibge", "municipio", "SE"]
    for keys, sub in work.groupby(group_cols):
        codigo_ibge, municipio, week = keys
        values = sub[metric].astype(float)
        median = float(values.median())
        rows.append({
            "codigo_ibge": codigo_ibge,
            "municipio": municipio,
            "SE": int(week),
            "metric": metric,
            "baseline_years_requested": ",".join(map(str, years)),
            "n_years": int(sub["ano"].nunique()),
            "median": median,
            "q25": float(values.quantile(0.25)),
            "q75": float(values.quantile(0.75)),
            "mad": float((values - median).abs().median()),
            "min": float(values.min()),
            "max": float(values.max()),
            "zero_semantics": "authorized_only_when_municipality_valid",
        })

    return pd.DataFrame(rows).sort_values(
        ["codigo_ibge", "SE"]
    ).reset_index(drop=True)
