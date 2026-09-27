# -*- coding: utf-8 -*-
from __future__ import annotations

import pandas as pd


REQUIRED_SIGNAL_COLUMNS = {
    "codigo_ibge",
    "municipio",
    "SE",
    "baseline_status",
    "trend_status",
    "anomaly_status",
}

REQUIRED_QUALITY_COLUMNS = {
    "codigo_ibge",
    "quality_status",
    "atraso_notificacao_mediana_dias",
    "desfecho_completo_percent",
    "inconsistencia_temporal_percent",
}


def build_signal_confidence(
    combined_signals: pd.DataFrame,
    quality: pd.DataFrame,
    stable_week: int,
    thresholds: dict,
) -> pd.DataFrame:
    missing_signal = REQUIRED_SIGNAL_COLUMNS.difference(combined_signals.columns)
    if missing_signal:
        raise ValueError(f"Sinais sem colunas obrigatórias: {sorted(missing_signal)}")
    missing_quality = REQUIRED_QUALITY_COLUMNS.difference(quality.columns)
    if missing_quality:
        raise ValueError(f"Qualidade sem colunas obrigatórias: {sorted(missing_quality)}")

    latest = combined_signals.loc[
        pd.to_numeric(combined_signals["SE"], errors="coerce").eq(int(stable_week))
    ].copy()
    if latest.empty:
        raise ValueError(f"Nenhum sinal encontrado para stable_week={stable_week}.")
    if latest["codigo_ibge"].duplicated().any():
        raise ValueError("Mais de um sinal por município na stable_week.")

    q = quality.copy()
    q["codigo_ibge"] = q["codigo_ibge"].astype("string").str.replace(r"\.0$", "", regex=True).str.zfill(7)
    latest["codigo_ibge"] = latest["codigo_ibge"].astype("string").str.replace(r"\.0$", "", regex=True).str.zfill(7)

    out = latest.merge(
        q,
        on="codigo_ibge",
        how="left",
        validate="one_to_one",
        suffixes=("", "_quality"),
    )

    high_delay = float(thresholds["notification_delay_high_max_days"])
    moderate_delay = float(thresholds["notification_delay_moderate_max_days"])
    high_outcome = float(thresholds["outcome_complete_high_min_percent"])
    moderate_outcome = float(thresholds["outcome_complete_moderate_min_percent"])
    high_inconsistency = float(thresholds["temporal_inconsistency_high_max_percent"])
    moderate_inconsistency = float(thresholds["temporal_inconsistency_moderate_max_percent"])

    def classify(row) -> str:
        if row.get("baseline_status") != "experimental":
            return "insufficient"
        if row.get("trend_status") != "experimental":
            return "insufficient"
        if row.get("quality_status") != "observed":
            return "insufficient"

        delay = pd.to_numeric(pd.Series([row.get("atraso_notificacao_mediana_dias")]), errors="coerce").iloc[0]
        outcome = pd.to_numeric(pd.Series([row.get("desfecho_completo_percent")]), errors="coerce").iloc[0]
        inconsistency = pd.to_numeric(pd.Series([row.get("inconsistencia_temporal_percent")]), errors="coerce").iloc[0]

        if pd.isna(delay) or pd.isna(outcome) or pd.isna(inconsistency):
            return "insufficient"

        if (
            delay > moderate_delay
            or outcome < moderate_outcome
            or inconsistency > moderate_inconsistency
        ):
            return "low_experimental"

        if (
            delay > high_delay
            or outcome < high_outcome
            or inconsistency > high_inconsistency
        ):
            return "moderate_experimental"

        return "high_experimental"

    out["signal_confidence"] = out.apply(classify, axis=1)
    out["confidence_model_status"] = "under_calibration"
    out["confidence_numeric_score"] = pd.NA
    out["risk_separation"] = True
    return out
