# -*- coding: utf-8 -*-
from __future__ import annotations

import json
import math
from pathlib import Path

import pandas as pd

from src.quality_metrics import parse_date
from src.sivep_pipeline import detect_text_format, digits, municipality_reference, normalize_week


def _quantile_days(values: pd.Series, q: float) -> float | None:
    numeric = pd.to_numeric(values, errors="coerce").dropna()
    numeric = numeric.loc[numeric.ge(0)]
    if numeric.empty:
        return None
    return float(numeric.quantile(q))


def _weeks_from_days(days: float | None) -> int | None:
    if days is None:
        return None
    return max(1, int(math.ceil(days / 7.0)))


def estimate_delay_based_stability(
    sivep_path: Path,
    population_path: Path,
    config_path: Path,
    chunksize: int = 100_000,
    quantile: float = 0.95,
) -> dict:
    cfg = json.loads(config_path.read_text(encoding="utf-8"))
    territory = cfg["territorial_scope"]
    time_cfg = cfg["time"]
    severity = cfg["severity"]
    quality = cfg["quality"]
    year = int(cfg["reference_year"])

    uf_field = territory["residence_uf_field"]
    mun_field = territory["municipality_code_candidates"][0]
    week_field = time_cfg["symptom_week_field"]
    symptom_field = time_cfg["symptom_date_field"]
    digitization_field = quality["digitization_date_field"]
    closure_field = quality["closure_date_field"]
    outcome_field = severity["outcome_field"]

    required = [
        uf_field,
        mun_field,
        week_field,
        symptom_field,
        digitization_field,
        closure_field,
        outcome_field,
    ]

    encoding, sep = detect_text_format(sivep_path)
    header = pd.read_csv(sivep_path, sep=sep, encoding=encoding, nrows=0)
    missing = [field for field in required if field not in header.columns]
    if missing:
        raise ValueError(f"Banco SIVEP sem campos para estabilidade: {missing}")

    ref = municipality_reference(population_path)
    valid_codes = set(ref["codigo_sivep_6"].tolist())

    case_delays: list[pd.Series] = []
    outcome_delays: list[pd.Series] = []
    observed_weeks: list[int] = []
    mt_rows = 0
    valid_case_delay_rows = 0
    valid_outcome_delay_rows = 0

    for chunk in pd.read_csv(
        sivep_path,
        sep=sep,
        encoding=encoding,
        dtype="string",
        usecols=required,
        chunksize=chunksize,
        low_memory=False,
    ):
        uf = chunk[uf_field].astype("string").str.strip().str.upper()
        chunk = chunk.loc[uf == territory["residence_uf_value"]].copy()
        mt_rows += len(chunk)
        if chunk.empty:
            continue

        chunk["codigo_sivep_6"] = chunk[mun_field].map(digits).str[:6]
        chunk = chunk.loc[chunk["codigo_sivep_6"].isin(valid_codes)].copy()
        if chunk.empty:
            continue

        symptom = parse_date(chunk[symptom_field])
        digitization = parse_date(chunk[digitization_field])
        closure = parse_date(chunk[closure_field])
        outcome = chunk[outcome_field].astype("string").str.strip()

        case_delay = (digitization - symptom).dt.days
        valid_case = case_delay.loc[case_delay.ge(0)]
        case_delays.append(valid_case)
        valid_case_delay_rows += int(valid_case.notna().sum())

        outcome_delay = (closure - symptom).dt.days
        valid_outcome = outcome_delay.loc[
            outcome.isin(["1", "2", "3"]) & outcome_delay.ge(0)
        ]
        outcome_delays.append(valid_outcome)
        valid_outcome_delay_rows += int(valid_outcome.notna().sum())

        weeks = chunk[week_field].map(lambda x: normalize_week(x, year)).dropna()
        observed_weeks.extend(int(x) for x in weeks.tolist())

    cases = pd.concat(case_delays, ignore_index=True) if case_delays else pd.Series(dtype=float)
    outcomes = pd.concat(outcome_delays, ignore_index=True) if outcome_delays else pd.Series(dtype=float)

    case_p50 = _quantile_days(cases, 0.50)
    case_p90 = _quantile_days(cases, 0.90)
    case_p95 = _quantile_days(cases, quantile)
    case_p99 = _quantile_days(cases, 0.99)

    outcome_p50 = _quantile_days(outcomes, 0.50)
    outcome_p90 = _quantile_days(outcomes, 0.90)
    outcome_p95 = _quantile_days(outcomes, quantile)
    outcome_p99 = _quantile_days(outcomes, 0.99)

    case_lag_weeks = _weeks_from_days(case_p95)
    outcome_lag_weeks = _weeks_from_days(outcome_p95)
    max_week = max(observed_weeks) if observed_weeks else None

    return {
        "method": "delay_distribution",
        "status": "provisional_until_vintage_backtest",
        "reference_year": year,
        "quantile_for_recommendation": quantile,
        "mt_rows_seen": int(mt_rows),
        "valid_case_delay_rows": int(valid_case_delay_rows),
        "valid_outcome_delay_rows": int(valid_outcome_delay_rows),
        "max_observed_week": max_week,
        "case_delay_days": {
            "p50": case_p50,
            "p90": case_p90,
            "p95": case_p95,
            "p99": case_p99,
        },
        "outcome_delay_days": {
            "p50": outcome_p50,
            "p90": outcome_p90,
            "p95": outcome_p95,
            "p99": outcome_p99,
        },
        "recommended_case_lag_weeks": case_lag_weeks,
        "recommended_outcome_lag_weeks": outcome_lag_weeks,
        "provisional_case_stable_week": (
            max(1, max_week - case_lag_weeks)
            if max_week is not None and case_lag_weeks is not None
            else None
        ),
        "provisional_outcome_stable_week": (
            max(1, max_week - outcome_lag_weeks)
            if max_week is not None and outcome_lag_weeks is not None
            else None
        ),
        "interpretation": (
            "Estimativa baseada na distribuição de atraso do snapshot atual. "
            "Não substitui backtesting por múltiplos vintages do banco vivo."
        ),
    }
