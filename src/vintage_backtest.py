# -*- coding: utf-8 -*-
from __future__ import annotations

import json
from datetime import date

from src.epi_calendar import epidemiological_week_start
from pathlib import Path

import pandas as pd


def load_vintages(root: Path) -> list[tuple[date, pd.DataFrame, dict]]:
    vintages = []
    if not root.exists():
        return vintages

    for folder in sorted(p for p in root.iterdir() if p.is_dir()):
        try:
            vintage_date = date.fromisoformat(folder.name)
        except ValueError:
            continue

        weekly_path = folder / "weekly.csv"
        metadata_path = folder / "metadata.json"
        if not weekly_path.exists() or not metadata_path.exists():
            continue

        weekly = pd.read_csv(weekly_path)
        metadata = json.loads(metadata_path.read_text(encoding="utf-8"))
        vintages.append((vintage_date, weekly, metadata))

    return sorted(vintages, key=lambda item: item[0])


def backtest_metric(
    root: Path,
    metric: str,
    tolerance: float = 0.05,
    min_observations: int = 5,
) -> tuple[pd.DataFrame, dict]:
    vintages = load_vintages(root)
    if len(vintages) < 3:
        raise ValueError(
            f"Backtesting requer pelo menos 3 vintages; encontrados {len(vintages)}."
        )

    latest_date, latest_weekly, latest_meta = vintages[-1]
    year = int(latest_meta.get("reference_year", 2026))

    if metric not in latest_weekly.columns:
        raise ValueError(f"Métrica ausente no vintage de referência: {metric}")

    reference = latest_weekly[["SE", metric]].copy()
    reference["SE"] = pd.to_numeric(reference["SE"], errors="coerce")
    reference[metric] = pd.to_numeric(reference[metric], errors="coerce")
    reference = reference.dropna().set_index("SE")[metric].to_dict()

    rows = []
    for vintage_date, weekly, metadata in vintages[:-1]:
        if metric not in weekly.columns:
            continue
        current = weekly[["SE", metric]].copy()
        current["SE"] = pd.to_numeric(current["SE"], errors="coerce")
        current[metric] = pd.to_numeric(current[metric], errors="coerce")
        current = current.dropna()

        for row in current.itertuples(index=False):
            week = int(row.SE)
            if week not in reference:
                continue
            value = float(getattr(row, metric))
            final = float(reference[week])
            week_start = epidemiological_week_start(year, week)
            age_days = (vintage_date - week_start).days
            if age_days < 0:
                continue
            age_weeks = age_days // 7
            absolute_revision = abs(final - value)
            relative_revision = absolute_revision / max(abs(final), 1.0)

            rows.append({
                "metric": metric,
                "vintage_date": vintage_date.isoformat(),
                "reference_vintage_date": latest_date.isoformat(),
                "SE": week,
                "age_weeks": int(age_weeks),
                "value_at_vintage": value,
                "reference_value": final,
                "absolute_revision": absolute_revision,
                "relative_revision": relative_revision,
            })

    detail = pd.DataFrame(rows)
    if detail.empty:
        raise ValueError("Nenhuma comparação válida entre vintages.")

    summary_rows = []
    for age, sub in detail.groupby("age_weeks"):
        revisions = sub["relative_revision"]
        summary_rows.append({
            "age_weeks": int(age),
            "observations": int(len(sub)),
            "revision_median": float(revisions.median()),
            "revision_p90": float(revisions.quantile(0.90)),
            "revision_max": float(revisions.max()),
        })
    summary = pd.DataFrame(summary_rows).sort_values("age_weeks").reset_index(drop=True)

    recommended = None
    for age in summary["age_weeks"].tolist():
        eligible = detail.loc[detail["age_weeks"] >= age, "relative_revision"]
        if len(eligible) < min_observations:
            continue
        if float(eligible.quantile(0.90)) <= tolerance:
            recommended = int(age)
            break

    report = {
        "method": "aggregate_vintage_revision",
        "metric": metric,
        "vintage_count": len(vintages),
        "reference_vintage_date": latest_date.isoformat(),
        "tolerance_relative_revision": tolerance,
        "min_observations": min_observations,
        "recommended_lag_weeks": recommended,
        "status": "calibrated_candidate" if recommended is not None else "insufficient_stability",
        "note": (
            "O último vintage é usado como referência operacional e ainda pode sofrer revisões futuras. "
            "Recalibrar a cada novo vintage."
        ),
    }
    return detail, summary, report
