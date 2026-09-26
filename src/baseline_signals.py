# -*- coding: utf-8 -*-
from __future__ import annotations

from dataclasses import dataclass
from math import log2
from typing import Iterable

import numpy as np
import pandas as pd

from src.epi_calendar import epidemiological_weeks_in_year


REQUIRED_HISTORY_COLUMNS = {
    "ANO",
    "SE",
    "codigo_ibge",
    "municipio",
    "populacao",
    "casos",
    "hospitalizacoes",
    "uti",
    "obitos",
}


@dataclass(frozen=True)
class BaselineConfig:
    target_year: int = 2026
    min_years: int = 3
    week_window: int = 2
    anomaly_z_threshold: float = 3.5
    trend_recent_weeks: int = 2
    trend_previous_weeks: int = 2
    trend_pseudocount: float = 0.5


def _ensure_history(history: pd.DataFrame) -> pd.DataFrame:
    missing = REQUIRED_HISTORY_COLUMNS.difference(history.columns)
    if missing:
        raise ValueError(f"Histórico sem colunas obrigatórias: {sorted(missing)}")

    out = history.copy()
    out["codigo_ibge"] = (
        out["codigo_ibge"]
        .astype("string")
        .str.replace(r"\.0$", "", regex=True)
        .str.zfill(7)
    )
    out["ANO"] = pd.to_numeric(out["ANO"], errors="raise").astype(int)
    out["SE"] = pd.to_numeric(out["SE"], errors="raise").astype(int)
    if not out["SE"].between(1, 53).all():
        raise ValueError("Histórico contém SE fora de 1..53.")
    if out.duplicated(["ANO", "SE", "codigo_ibge"]).any():
        raise ValueError("Histórico contém duplicidade em ANO+SE+codigo_ibge.")

    numeric = ["populacao", "casos", "hospitalizacoes", "uti", "obitos"]
    for col in numeric:
        out[col] = pd.to_numeric(out[col], errors="raise")
        if (out[col] < 0).any():
            raise ValueError(f"Histórico contém valor negativo em {col}.")

    if (out["populacao"] <= 0).any():
        raise ValueError("Histórico contém população não positiva.")

    out["incidencia_srag_100k"] = out["casos"] / out["populacao"] * 100000.0
    out["hospitalizacao_100k"] = out["hospitalizacoes"] / out["populacao"] * 100000.0
    out["uti_100k"] = out["uti"] / out["populacao"] * 100000.0
    out["obito_100k"] = out["obitos"] / out["populacao"] * 100000.0
    return out


def _validate_complete_history(data: pd.DataFrame, years: list[int]) -> None:
    selected = data.loc[data["ANO"].isin(years)].copy()
    if selected.empty:
        raise ValueError(f"Nenhum dado disponível para os anos históricos selecionados: {years}")

    codes = sorted(selected["codigo_ibge"].unique().tolist())
    problems: list[str] = []
    for year in years:
        expected_weeks = set(range(1, epidemiological_weeks_in_year(year) + 1))
        year_data = selected.loc[selected["ANO"] == year]
        for code in codes:
            observed = set(
                year_data.loc[year_data["codigo_ibge"] == code, "SE"].astype(int).tolist()
            )
            missing = sorted(expected_weeks.difference(observed))
            extra = sorted(observed.difference(expected_weeks))
            if missing or extra:
                problems.append(
                    f"{year}/{code}: missing={missing[:5]} extra={extra[:5]}"
                )
                if len(problems) >= 10:
                    break
        if len(problems) >= 10:
            break

    if problems:
        raise ValueError(
            "Histórico não possui semanas explícitas completas. "
            "Ausência de linha não pode ser tratada como zero. Exemplos: "
            + "; ".join(problems)
        )


def _validate_current_coverage(data: pd.DataFrame, year: int, stable_week: int) -> None:
    current = data.loc[data["ANO"] == year]
    if current.empty:
        raise ValueError(f"Sem painel semanal para o ano atual {year}.")
    expected = set(range(1, int(stable_week) + 1))
    problems: list[str] = []
    for code, group in current.groupby("codigo_ibge", sort=False):
        observed = set(group["SE"].astype(int).tolist())
        missing = sorted(expected.difference(observed))
        if missing:
            problems.append(f"{code}: missing={missing[:5]}")
            if len(problems) >= 10:
                break
    if problems:
        raise ValueError(
            "Painel atual não possui zeros explícitos até a stable_week. Exemplos: "
            + "; ".join(problems)
        )


def _circular_week_distance(a: pd.Series, week: int) -> pd.Series:
    direct = (a - week).abs()
    return np.minimum(direct, 53 - direct)


def build_seasonal_baseline(
    history: pd.DataFrame,
    metric: str,
    target_year: int = 2026,
    min_years: int = 3,
    week_window: int = 2,
    history_years: Iterable[int] | None = None,
) -> pd.DataFrame:
    data = _ensure_history(history)
    if metric not in data.columns:
        raise ValueError(f"Métrica não disponível: {metric}")
    if min_years < 2:
        raise ValueError("min_years deve ser >= 2.")
    if week_window < 0 or week_window > 10:
        raise ValueError("week_window fora do intervalo 0..10.")

    available_before_target = sorted(data.loc[data["ANO"] < target_year, "ANO"].unique().tolist())
    selected_years = sorted({int(y) for y in (history_years or available_before_target)})
    selected_years = [y for y in selected_years if y < target_year]
    if len(selected_years) < min_years:
        raise ValueError(
            f"Anos históricos selecionados insuficientes: {selected_years}; mínimo={min_years}."
        )
    hist = data.loc[data["ANO"].isin(selected_years)].copy()
    _validate_complete_history(hist, selected_years)
    municipalities = (
        data.loc[data["ANO"] == target_year, ["codigo_ibge", "municipio"]]
        .drop_duplicates("codigo_ibge")
    )
    if municipalities.empty:
        municipalities = hist[["codigo_ibge", "municipio"]].drop_duplicates("codigo_ibge")

    rows = []
    for mun in municipalities.itertuples(index=False):
        mh = hist.loc[hist["codigo_ibge"] == mun.codigo_ibge].copy()
        available_years = sorted(mh["ANO"].unique().tolist())

        for week in range(1, 54):
            seasonal = mh.loc[_circular_week_distance(mh["SE"], week) <= week_window, metric]
            seasonal = pd.to_numeric(seasonal, errors="coerce").dropna()

            year_count = len(available_years)
            if year_count < min_years or seasonal.empty:
                rows.append({
                    "codigo_ibge": mun.codigo_ibge,
                    "municipio": mun.municipio,
                    "SE": week,
                    "metric": metric,
                    "historical_years": year_count,
                    "historical_observations": int(len(seasonal)),
                    "baseline_median": np.nan,
                    "baseline_q25": np.nan,
                    "baseline_q75": np.nan,
                    "baseline_mad": np.nan,
                    "historical_nonzero_frequency": np.nan,
                    "baseline_status": "insufficient_history",
                })
                continue

            median = float(seasonal.median())
            mad = float((seasonal - median).abs().median())
            rows.append({
                "codigo_ibge": mun.codigo_ibge,
                "municipio": mun.municipio,
                "SE": week,
                "metric": metric,
                "historical_years": year_count,
                "historical_observations": int(len(seasonal)),
                "baseline_median": median,
                "baseline_q25": float(seasonal.quantile(0.25)),
                "baseline_q75": float(seasonal.quantile(0.75)),
                "baseline_mad": mad,
                "historical_nonzero_frequency": float((seasonal > 0).mean()),
                "baseline_status": "experimental",
            })

    return pd.DataFrame(rows)


def add_anomaly_signal(
    current_weekly: pd.DataFrame,
    baseline: pd.DataFrame,
    metric: str,
    stable_week: int,
    robust_z_threshold: float = 3.5,
) -> pd.DataFrame:
    current = _ensure_history(current_weekly)
    current_year = int(current["ANO"].max())
    _validate_current_coverage(current, current_year, stable_week)
    current = current.loc[
        (current["ANO"] == current_year) & (current["SE"] <= stable_week)
    ].copy()

    base = baseline.loc[baseline["metric"] == metric].copy()
    merged = current.merge(
        base,
        on=["codigo_ibge", "municipio", "SE"],
        how="left",
        validate="one_to_one",
    )

    observed = pd.to_numeric(merged[metric], errors="coerce")
    median = pd.to_numeric(merged["baseline_median"], errors="coerce")
    mad = pd.to_numeric(merged["baseline_mad"], errors="coerce")
    scale = 1.4826 * mad

    merged["observed_value"] = observed
    merged["ratio_to_baseline"] = np.where(
        median > 0,
        observed / median,
        np.where(observed == 0, 1.0, np.nan),
    )
    merged["robust_z"] = np.where(scale > 0, (observed - median) / scale, np.nan)

    def classify(row) -> str:
        if row.get("baseline_status") != "experimental":
            return "insufficient_history"
        rz = row.get("robust_z")
        obs = row.get("observed_value")
        q75 = row.get("baseline_q75")
        med = row.get("baseline_median")
        if pd.notna(rz):
            if rz >= robust_z_threshold:
                return "above_expected_experimental"
            if rz <= -robust_z_threshold:
                return "below_expected_experimental"
            return "within_expected_experimental"

        # MAD zero: não fabricar z-score. Apenas registrar desvio determinístico.
        if pd.notna(obs) and pd.notna(q75) and obs > q75:
            return "above_expected_zero_mad_experimental"
        if pd.notna(obs) and pd.notna(med) and obs < med:
            return "below_expected_zero_mad_experimental"
        return "within_expected_zero_mad_experimental"

    merged["anomaly_status"] = merged.apply(classify, axis=1)
    merged["anomaly_model_status"] = "under_calibration"
    return merged


def build_trend_signals(
    current_weekly: pd.DataFrame,
    metric: str,
    stable_week: int,
    recent_weeks: int = 2,
    previous_weeks: int = 2,
    pseudocount: float = 0.5,
) -> pd.DataFrame:
    data = _ensure_history(current_weekly)
    year = int(data["ANO"].max())
    _validate_current_coverage(data, year, stable_week)
    data = data.loc[(data["ANO"] == year) & (data["SE"] <= stable_week)].copy()

    needed = recent_weeks + previous_weeks
    if stable_week < needed:
        raise ValueError(
            f"stable_week={stable_week} insuficiente para {needed} semanas de tendência."
        )

    recent_start = stable_week - recent_weeks + 1
    previous_end = recent_start - 1
    previous_start = previous_end - previous_weeks + 1

    rows = []
    for code, group in data.groupby("codigo_ibge", sort=True):
        name = str(group["municipio"].iloc[0])
        recent = group.loc[group["SE"].between(recent_start, stable_week), metric]
        previous = group.loc[group["SE"].between(previous_start, previous_end), metric]

        if len(recent) != recent_weeks or len(previous) != previous_weeks:
            rows.append({
                "codigo_ibge": code,
                "municipio": name,
                "stable_week": stable_week,
                "metric": metric,
                "recent_mean": np.nan,
                "previous_mean": np.nan,
                "trend_ratio": np.nan,
                "trend_log2": np.nan,
                "trend_status": "insufficient_complete_weeks",
            })
            continue

        recent_mean = float(pd.to_numeric(recent).mean())
        previous_mean = float(pd.to_numeric(previous).mean())
        ratio = (recent_mean + pseudocount) / (previous_mean + pseudocount)
        rows.append({
            "codigo_ibge": code,
            "municipio": name,
            "stable_week": stable_week,
            "metric": metric,
            "recent_mean": recent_mean,
            "previous_mean": previous_mean,
            "trend_ratio": ratio,
            "trend_log2": log2(ratio),
            "trend_status": "experimental",
        })

    return pd.DataFrame(rows)


def combine_surveillance_signals(
    anomalies: pd.DataFrame,
    trends: pd.DataFrame,
) -> pd.DataFrame:
    trend_cols = [
        "codigo_ibge",
        "trend_ratio",
        "trend_log2",
        "trend_status",
        "recent_mean",
        "previous_mean",
    ]
    out = anomalies.merge(
        trends[trend_cols],
        on="codigo_ibge",
        how="left",
        validate="many_to_one",
    )
    out["signal_status"] = np.where(
        (out["anomaly_status"].astype("string").str.startswith("above_expected"))
        & (out["trend_log2"] > 0),
        "elevated_and_rising_experimental",
        np.where(
            out["anomaly_status"].astype("string").str.startswith("above_expected"),
            "elevated_not_rising_experimental",
            np.where(
                out["trend_log2"] > 0,
                "rising_without_baseline_excess_experimental",
                "no_combined_signal_experimental",
            ),
        ),
    )
    out["validated_for_operational_alert"] = False
    return out
