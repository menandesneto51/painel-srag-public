# -*- coding: utf-8 -*-
from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd

from src.baseline_signals import add_anomaly_signal, build_seasonal_baseline


@dataclass(frozen=True)
class BacktestResult:
    summary: pd.DataFrame
    predictions: pd.DataFrame


def _safe_ratio(numerator: int, denominator: int) -> float | None:
    if denominator <= 0:
        return None
    return float(numerator / denominator)


def _future_max(values: pd.Series, window: int) -> pd.Series:
    arr = pd.to_numeric(values, errors="coerce").to_numpy(dtype=float)
    result = np.full(len(arr), np.nan)
    for i in range(len(arr)):
        start = i + 1
        end = start + window
        if end > len(arr):
            continue
        segment = arr[start:end]
        if len(segment) == window:
            result[i] = np.nanmax(segment)
    return pd.Series(result, index=values.index)


def backtest_anomaly_thresholds(
    panel: pd.DataFrame,
    metric: str = "hospitalizacoes",
    min_training_years: int = 3,
    week_window: int = 2,
    thresholds: list[float] | tuple[float, ...] = (2.5, 3.0, 3.5, 4.0),
    future_window_weeks: int = 2,
    event_quantile: float = 0.90,
) -> BacktestResult:
    required = {
        "ANO", "SE", "codigo_ibge", "municipio", "populacao",
        "casos", "hospitalizacoes", "uti", "obitos",
    }
    missing = required.difference(panel.columns)
    if missing:
        raise ValueError(f"Painel de backtesting sem colunas: {sorted(missing)}")
    if metric not in panel.columns:
        raise ValueError(f"Métrica não disponível: {metric}")
    if min_training_years < 2:
        raise ValueError("min_training_years deve ser >= 2.")
    if not (0.5 < event_quantile < 1):
        raise ValueError("event_quantile deve estar entre 0,5 e 1.")
    if future_window_weeks < 1:
        raise ValueError("future_window_weeks deve ser >= 1.")

    data = panel.copy()
    data["ANO"] = pd.to_numeric(data["ANO"], errors="raise").astype(int)
    data["SE"] = pd.to_numeric(data["SE"], errors="raise").astype(int)
    data["codigo_ibge"] = data["codigo_ibge"].astype("string").str.zfill(7)
    data[metric] = pd.to_numeric(data[metric], errors="raise")

    years = sorted(data["ANO"].unique().tolist())
    prediction_parts: list[pd.DataFrame] = []

    for holdout_year in years:
        training_years = [year for year in years if year < holdout_year]
        if len(training_years) < min_training_years:
            continue

        training = data.loc[data["ANO"].isin(training_years)].copy()
        current = data.loc[data["ANO"] == holdout_year].copy()
        if current.empty:
            continue

        stable_week = int(current["SE"].max())
        baseline = build_seasonal_baseline(
            training,
            metric=metric,
            target_year=holdout_year,
            min_years=min_training_years,
            week_window=week_window,
            history_years=training_years,
        )
        anomaly = add_anomaly_signal(
            current,
            baseline,
            metric=metric,
            stable_week=stable_week,
            robust_z_threshold=min(float(t) for t in thresholds),
        )

        thresholds_by_municipality = (
            training.groupby("codigo_ibge")[metric]
            .quantile(event_quantile)
            .rename("event_threshold")
        )

        parts = []
        for code, group in current.groupby("codigo_ibge", sort=False):
            ordered = group.sort_values("SE").copy()
            ordered["future_max_activity"] = _future_max(
                ordered[metric], future_window_weeks
            )
            threshold = thresholds_by_municipality.get(code, np.nan)
            ordered["event_threshold"] = threshold
            ordered["future_high_activity"] = (
                ordered["future_max_activity"] >= threshold
            )
            parts.append(
                ordered[[
                    "codigo_ibge",
                    "SE",
                    "future_max_activity",
                    "event_threshold",
                    "future_high_activity",
                ]]
            )

        labels = pd.concat(parts, ignore_index=True)
        evaluated = anomaly.merge(
            labels,
            on=["codigo_ibge", "SE"],
            how="left",
            validate="one_to_one",
        )
        evaluated["holdout_year"] = holdout_year
        evaluated["training_years"] = ",".join(map(str, training_years))
        evaluated["zero_mad_above_expected"] = (
            evaluated["anomaly_status"]
            .astype("string")
            .eq("above_expected_zero_mad_experimental")
        )
        prediction_parts.append(evaluated)

    if not prediction_parts:
        raise ValueError(
            "Nenhum holdout possui anos de treinamento suficientes para backtesting."
        )

    predictions = pd.concat(prediction_parts, ignore_index=True)
    rows = []
    for threshold in thresholds:
        valid = predictions.loc[
            predictions["robust_z"].notna()
            & predictions["future_high_activity"].notna()
        ].copy()
        signal = valid["robust_z"] >= float(threshold)
        event = valid["future_high_activity"].astype(bool)

        tp = int((signal & event).sum())
        fp = int((signal & ~event).sum())
        fn = int((~signal & event).sum())
        tn = int((~signal & ~event).sum())

        rows.append({
            "robust_z_threshold": float(threshold),
            "observations": int(len(valid)),
            "tp": tp,
            "fp": fp,
            "fn": fn,
            "tn": tn,
            "sensitivity": _safe_ratio(tp, tp + fn),
            "specificity": _safe_ratio(tn, tn + fp),
            "precision_ppv": _safe_ratio(tp, tp + fp),
            "negative_predictive_value": _safe_ratio(tn, tn + fn),
            "signal_rate": _safe_ratio(tp + fp, len(valid)),
            "event_rate": _safe_ratio(tp + fn, len(valid)),
            "backtest_status": "experimental_internal_calibration",
        })

    summary = pd.DataFrame(rows)
    return BacktestResult(summary=summary, predictions=predictions)
