# -*- coding: utf-8 -*-
from __future__ import annotations

import json
from pathlib import Path

import pandas as pd


DEFAULT_MAD_CONSTANT = 0.6744897501960817
DEFAULT_IQR_TO_SIGMA = 1.3489795003921634


def robust_deviation(
    observed: float,
    median: float,
    mad: float,
    q25: float,
    q75: float,
    mad_constant: float = DEFAULT_MAD_CONSTANT,
    iqr_to_sigma: float = DEFAULT_IQR_TO_SIGMA,
) -> tuple[float | None, str]:
    observed = float(observed)
    median = float(median)
    mad = float(mad)
    q25 = float(q25)
    q75 = float(q75)

    if mad > 0:
        return mad_constant * (observed - median) / mad, "MAD"

    iqr = q75 - q25
    if iqr > 0:
        sigma = iqr / iqr_to_sigma
        return (observed - median) / sigma, "IQR"

    # Sem dispersão histórica mensurável não há escala defensável.
    return None, "NO_DISPERSION"


def _apply_persistence(
    table: pd.DataFrame,
    persistence_weeks: int,
) -> pd.DataFrame:
    result = table.sort_values("SE").copy()
    candidate = result["candidate_elevated"].fillna(False).astype(bool)
    persistent = pd.Series(False, index=result.index)

    if persistence_weeks <= 1:
        persistent = candidate
    else:
        run = 0
        previous_week = None
        for idx, row in result.iterrows():
            week = int(row["SE"])
            is_candidate = bool(row["candidate_elevated"])
            consecutive = previous_week is not None and week == previous_week + 1
            if is_candidate:
                run = run + 1 if consecutive else 1
            else:
                run = 0
            if run >= persistence_weeks:
                persistent.loc[idx] = True
            previous_week = week

    result["persistent_elevated"] = persistent
    result["signal_status"] = "within_expected"
    result.loc[result["candidate_elevated"], "signal_status"] = "candidate_elevated"
    result.loc[result["persistent_elevated"], "signal_status"] = "persistent_elevated"
    result.loc[result["candidate_low"], "signal_status"] = "candidate_low"
    result.loc[result["insufficient_baseline"], "signal_status"] = "insufficient_baseline"
    result.loc[result["dispersion_method"].eq("NO_DISPERSION"), "signal_status"] = "no_historical_dispersion"
    return result


def detect_robust_anomalies(
    observed: pd.DataFrame,
    baseline: pd.DataFrame,
    metric: str,
    stable_week: int,
    z_threshold: float = 3.5,
    persistence_weeks: int = 2,
    min_baseline_years: int = 3,
) -> pd.DataFrame:
    required_observed = {"SE", metric}
    required_baseline = {"SE", "metric", "n_years", "median", "q25", "q75", "mad"}
    missing_obs = required_observed.difference(observed.columns)
    missing_base = required_baseline.difference(baseline.columns)
    if missing_obs:
        raise ValueError(f"Observado sem colunas: {sorted(missing_obs)}")
    if missing_base:
        raise ValueError(f"Baseline sem colunas: {sorted(missing_base)}")
    if stable_week < 1:
        raise ValueError("stable_week deve ser >= 1.")
    if z_threshold <= 0:
        raise ValueError("z_threshold deve ser positivo.")
    if persistence_weeks < 1:
        raise ValueError("persistence_weeks deve ser >= 1.")

    base = baseline.loc[baseline["metric"].astype(str) == str(metric)].copy()
    obs = observed[["SE", metric]].copy()
    obs["SE"] = pd.to_numeric(obs["SE"], errors="coerce")
    obs[metric] = pd.to_numeric(obs[metric], errors="coerce")
    obs = obs.dropna(subset=["SE", metric])
    obs["SE"] = obs["SE"].astype(int)
    obs = obs.loc[obs["SE"] <= int(stable_week)].copy()
    obs = obs.rename(columns={metric: "observed"})

    merged = obs.merge(base, on="SE", how="left", validate="one_to_one")
    rows = []
    for row in merged.itertuples(index=False):
        n_years = 0 if pd.isna(row.n_years) else int(row.n_years)
        insufficient = n_years < int(min_baseline_years)
        score = None
        method = "INSUFFICIENT"
        if not insufficient and all(
            not pd.isna(value)
            for value in (row.median, row.mad, row.q25, row.q75)
        ):
            score, method = robust_deviation(
                row.observed,
                row.median,
                row.mad,
                row.q25,
                row.q75,
            )

        median = None if pd.isna(row.median) else float(row.median)
        observed_value = float(row.observed)
        excess = None if median is None else observed_value - median
        relative_excess = (
            None
            if median is None or median <= 0
            else (observed_value - median) / median
        )

        candidate_elevated = bool(
            not insufficient
            and score is not None
            and score >= z_threshold
            and excess is not None
            and excess > 0
        )
        candidate_low = bool(
            not insufficient
            and score is not None
            and score <= -z_threshold
            and excess is not None
            and excess < 0
        )

        rows.append({
            "SE": int(row.SE),
            "metric": metric,
            "observed": observed_value,
            "baseline_median": median,
            "baseline_q25": None if pd.isna(row.q25) else float(row.q25),
            "baseline_q75": None if pd.isna(row.q75) else float(row.q75),
            "baseline_mad": None if pd.isna(row.mad) else float(row.mad),
            "baseline_n_years": n_years,
            "excess_absolute": excess,
            "excess_relative": relative_excess,
            "robust_deviation": score,
            "dispersion_method": method,
            "candidate_elevated": candidate_elevated,
            "candidate_low": candidate_low,
            "insufficient_baseline": insufficient,
            "stable_week_cutoff": int(stable_week),
            "model_status": "experimental",
        })

    return _apply_persistence(pd.DataFrame(rows), persistence_weeks)


def load_anomaly_config(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))
