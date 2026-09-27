# -*- coding: utf-8 -*-
from __future__ import annotations

import pandas as pd


def build_silence_signals(
    current_weekly: pd.DataFrame,
    baseline: pd.DataFrame,
    confidence: pd.DataFrame,
    stable_week: int,
    metric: str = "hospitalizacoes",
    window_weeks: int = 2,
    expected_nonzero_frequency_min: float = 0.60,
) -> pd.DataFrame:
    if stable_week < window_weeks:
        raise ValueError("stable_week insuficiente para a janela de silêncio.")
    for required in ("codigo_ibge", "municipio", "SE", metric):
        if required not in current_weekly.columns:
            raise ValueError(f"Painel atual sem coluna: {required}")
    for required in (
        "codigo_ibge",
        "SE",
        "metric",
        "baseline_status",
        "baseline_median",
        "historical_nonzero_frequency",
    ):
        if required not in baseline.columns:
            raise ValueError(f"Baseline sem coluna: {required}")
    if "signal_confidence" not in confidence.columns:
        raise ValueError("Camada de confiança sem signal_confidence.")

    start_week = stable_week - window_weeks + 1
    current = current_weekly.loc[
        pd.to_numeric(current_weekly["SE"], errors="coerce").between(start_week, stable_week)
    ].copy()
    base = baseline.loc[
        (baseline["metric"] == metric)
        & pd.to_numeric(baseline["SE"], errors="coerce").between(start_week, stable_week)
    ].copy()

    rows = []
    for code, group in current.groupby("codigo_ibge", sort=True):
        name = str(group["municipio"].iloc[0])
        recent_values = pd.to_numeric(group[metric], errors="coerce")
        if len(group) != window_weeks or recent_values.isna().any():
            recent_sum = None
        else:
            recent_sum = float(recent_values.sum())

        b = base.loc[base["codigo_ibge"].astype("string") == str(code)]
        valid_b = b.loc[b["baseline_status"] == "experimental"]
        baseline_complete = len(valid_b) == window_weeks

        median_mean = (
            float(pd.to_numeric(valid_b["baseline_median"], errors="coerce").mean())
            if baseline_complete else None
        )
        nonzero_mean = (
            float(pd.to_numeric(valid_b["historical_nonzero_frequency"], errors="coerce").mean())
            if baseline_complete else None
        )

        conf_row = confidence.loc[confidence["codigo_ibge"].astype("string") == str(code)]
        conf = (
            str(conf_row.iloc[0]["signal_confidence"])
            if len(conf_row) == 1 else "insufficient"
        )

        if recent_sum is None or not baseline_complete:
            status = "insufficient"
        elif recent_sum > 0:
            status = "activity_present"
        elif median_mean is not None and median_mean <= 0 and (
            nonzero_mean is None or nonzero_mean < expected_nonzero_frequency_min
        ):
            status = "expected_sparse_or_zero"
        elif nonzero_mean is not None and nonzero_mean >= expected_nonzero_frequency_min:
            if conf in {"high_experimental", "moderate_experimental"}:
                status = "silence_signal_under_review"
            else:
                status = "zero_observed_low_confidence"
        else:
            status = "zero_observed_context_uncertain"

        rows.append({
            "codigo_ibge": code,
            "municipio": name,
            "stable_week": int(stable_week),
            "window_weeks": int(window_weeks),
            "metric": metric,
            "recent_sum": recent_sum,
            "baseline_median_mean": median_mean,
            "historical_nonzero_frequency_mean": nonzero_mean,
            "signal_confidence": conf,
            "silence_status": status,
            "silence_model_status": "under_calibration",
            "validated_for_operational_alert": False,
        })

    return pd.DataFrame(rows)
