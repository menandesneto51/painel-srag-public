# -*- coding: utf-8 -*-
from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pandas as pd


CLASS_ORDER = {
    "insufficient": 0,
    "low": 1,
    "moderate": 2,
    "high": 3,
}


def classify_numeric(value: float | int | None, rule: dict) -> str:
    if value is None or pd.isna(value):
        return "insufficient"

    value = float(value)
    direction = rule["direction"]

    if direction == "higher_better":
        if value >= float(rule["high"]):
            return "high"
        if value >= float(rule["moderate"]):
            return "moderate"
        if value >= float(rule["low"]):
            return "low"
        return "insufficient"

    if direction == "lower_better":
        if value <= float(rule["high"]):
            return "high"
        if value <= float(rule["moderate"]):
            return "moderate"
        if value <= float(rule["low"]):
            return "low"
        return "insufficient"

    raise ValueError(f"Direção desconhecida: {direction}")


def classify_stability(is_stable: bool | None) -> str:
    if is_stable is True:
        return "high"
    if is_stable is False:
        return "insufficient"
    return "insufficient"


def overall_confidence(
    components: dict[str, str],
    required_dimensions: list[str],
) -> str:
    missing = [name for name in required_dimensions if name not in components]
    if missing:
        raise ValueError(
            "Dimensões essenciais ausentes: " + ", ".join(sorted(missing))
        )

    classes = [components[name] for name in required_dimensions]
    invalid = [value for value in classes if value not in CLASS_ORDER]
    if invalid:
        raise ValueError(f"Classes inválidas: {invalid}")

    return min(classes, key=lambda value: CLASS_ORDER[value])


def build_confidence_profile(
    *,
    config: dict,
    is_stable: bool | None,
    volume: float | int | None,
    outcome_completeness_percent: float | None,
    notification_delay_median_days: float | None,
    temporal_inconsistency_percent: float | None,
    laboratory_coverage_percent: float | None = None,
    vintage_count: int | None = None,
    baseline_year_count: int | None = None,
) -> dict[str, Any]:
    thresholds = config["thresholds"]

    components = {
        "stability": classify_stability(is_stable),
        "volume": classify_numeric(volume, thresholds["volume"]),
        "outcome_completeness": classify_numeric(
            outcome_completeness_percent,
            thresholds["outcome_completeness"],
        ),
        "timeliness": classify_numeric(
            notification_delay_median_days,
            thresholds["timeliness"],
        ),
        "temporal_consistency": classify_numeric(
            temporal_inconsistency_percent,
            thresholds["temporal_consistency"],
        ),
        "laboratory_coverage": classify_numeric(
            laboratory_coverage_percent,
            thresholds["laboratory_coverage"],
        ),
        "vintage_depth": classify_numeric(
            vintage_count,
            thresholds["vintage_depth"],
        ),
        "baseline_depth": classify_numeric(
            baseline_year_count,
            thresholds["baseline_depth"],
        ),
    }

    overall = overall_confidence(
        components,
        list(config["required_dimensions"]),
    )

    reporting_required = [
        "outcome_completeness",
        "timeliness",
        "temporal_consistency",
    ]
    reporting_quality = overall_confidence(
        components,
        reporting_required,
    )

    limiting = [
        name
        for name in config["required_dimensions"]
        if components[name] == overall
    ]

    return {
        "confidence_class": overall,
        "reporting_quality_class": reporting_quality,
        "limiting_dimensions": limiting,
        "components": components,
        "model_id": config["model_id"],
        "model_version": config["version"],
        "model_status": config["status"],
        "numeric_score": None,
        "risk_separation": True,
    }


def load_confidence_config(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))
