# -*- coding: utf-8 -*-
from __future__ import annotations

from typing import Iterable

import numpy as np
import pandas as pd


PRESSURE_REQUIRED_COLUMNS = {
    "codigo_ibge",
    "reference_week",
    "pressure_status",
    "validation_status",
    "source_scope",
}


def _ibge(series: pd.Series) -> pd.Series:
    return (
        series.astype("string")
        .str.replace(r"\.0$", "", regex=True)
        .str.zfill(7)
    )


def summarize_virology_window(
    virology_municipal_weekly: pd.DataFrame | None,
    stable_week: int,
    window_weeks: int = 2,
    excluded_dominant_agents: Iterable[str] = (
        "Sem agente detectado/codificado",
        "Detectável sem agente codificado",
    ),
) -> pd.DataFrame:
    columns = [
        "codigo_ibge",
        "virology_window_start",
        "virology_window_end",
        "virology_records_srag",
        "virology_pcr_result_available",
        "virology_pcr_conclusive",
        "virology_pcr_detectable",
        "virology_coverage_molecular_percent",
        "virology_named_agent_detections",
        "virology_unclassified_detectable_detections",
        "virology_dominant_agent",
        "virology_dominant_agent_detections",
        "virology_status",
    ]
    if virology_municipal_weekly is None or virology_municipal_weekly.empty:
        return pd.DataFrame(columns=columns)
    if stable_week < window_weeks:
        raise ValueError("stable_week insuficiente para janela virológica.")

    required = {
        "codigo_ibge",
        "SE",
        "virus",
        "deteccoes",
        "registros_srag",
        "pcr_resultado_disponivel",
        "pcr_conclusivo",
        "pcr_detectavel",
    }
    missing = required.difference(virology_municipal_weekly.columns)
    if missing:
        raise ValueError(f"Virologia municipal sem colunas: {sorted(missing)}")

    start = stable_week - window_weeks + 1
    data = virology_municipal_weekly.copy()
    data["codigo_ibge"] = _ibge(data["codigo_ibge"])
    data["SE"] = pd.to_numeric(data["SE"], errors="raise").astype(int)
    data = data.loc[data["SE"].between(start, stable_week)].copy()
    if data.empty:
        return pd.DataFrame(columns=columns)

    for col in (
        "deteccoes",
        "registros_srag",
        "pcr_resultado_disponivel",
        "pcr_conclusivo",
        "pcr_detectavel",
    ):
        data[col] = pd.to_numeric(data[col], errors="coerce").fillna(0)

    # Denominadores laboratoriais se repetem em cada linha de vírus.
    # Deduplicar por município + SE antes de agregá-los.
    denominators = (
        data[[
            "codigo_ibge",
            "SE",
            "registros_srag",
            "pcr_resultado_disponivel",
            "pcr_conclusivo",
            "pcr_detectavel",
        ]]
        .drop_duplicates(["codigo_ibge", "SE"])
        .groupby("codigo_ibge", as_index=False)
        .agg(
            virology_records_srag=("registros_srag", "sum"),
            virology_pcr_result_available=("pcr_resultado_disponivel", "sum"),
            virology_pcr_conclusive=("pcr_conclusivo", "sum"),
            virology_pcr_detectable=("pcr_detectavel", "sum"),
        )
    )
    denominators["virology_coverage_molecular_percent"] = np.where(
        denominators["virology_records_srag"] > 0,
        denominators["virology_pcr_result_available"]
        / denominators["virology_records_srag"]
        * 100.0,
        np.nan,
    )

    excluded = set(map(str, excluded_dominant_agents))
    detections = (
        data.groupby(["codigo_ibge", "virus"], as_index=False)["deteccoes"].sum()
    )
    named = detections.loc[
        (~detections["virus"].astype("string").isin(excluded))
        & (detections["deteccoes"] > 0)
    ].copy()
    unclassified = detections.loc[
        detections["virus"].astype("string").eq("Detectável sem agente codificado")
    ].copy()

    named_total = (
        named.groupby("codigo_ibge", as_index=False)["deteccoes"]
        .sum()
        .rename(columns={"deteccoes": "virology_named_agent_detections"})
    )
    unclassified_total = (
        unclassified.groupby("codigo_ibge", as_index=False)["deteccoes"]
        .sum()
        .rename(columns={"deteccoes": "virology_unclassified_detectable_detections"})
    )

    if named.empty:
        dominant = pd.DataFrame(
            columns=[
                "codigo_ibge",
                "virology_dominant_agent",
                "virology_dominant_agent_detections",
            ]
        )
    else:
        named = named.sort_values(
            ["codigo_ibge", "deteccoes", "virus"],
            ascending=[True, False, True],
        )
        dominant = (
            named.drop_duplicates("codigo_ibge")
            [["codigo_ibge", "virus", "deteccoes"]]
            .rename(columns={
                "virus": "virology_dominant_agent",
                "deteccoes": "virology_dominant_agent_detections",
            })
        )

    out = denominators.merge(named_total, on="codigo_ibge", how="left")
    out = out.merge(unclassified_total, on="codigo_ibge", how="left")
    out = out.merge(dominant, on="codigo_ibge", how="left")
    out["virology_named_agent_detections"] = (
        out["virology_named_agent_detections"].fillna(0).astype(int)
    )
    out["virology_unclassified_detectable_detections"] = (
        out["virology_unclassified_detectable_detections"].fillna(0).astype(int)
    )
    out["virology_dominant_agent_detections"] = (
        out["virology_dominant_agent_detections"].fillna(0).astype(int)
    )
    out["virology_window_start"] = int(start)
    out["virology_window_end"] = int(stable_week)
    out["virology_status"] = np.where(
        out["virology_records_srag"] <= 0,
        "no_srag_records",
        np.where(
            out["virology_pcr_result_available"] <= 0,
            "no_molecular_result_available",
            np.where(
                out["virology_named_agent_detections"] > 0,
                "named_agent_detected",
                np.where(
                    out["virology_unclassified_detectable_detections"] > 0,
                    "detectable_without_named_agent",
                    "no_named_agent_detected",
                ),
            ),
        ),
    )
    return out[columns]


def validate_healthcare_pressure(
    pressure: pd.DataFrame | None,
    stable_week: int,
) -> pd.DataFrame:
    columns = [
        "codigo_ibge",
        "reference_week",
        "pressure_status",
        "validation_status",
        "source_scope",
        "pressure_evidence",
    ]
    if pressure is None or pressure.empty:
        return pd.DataFrame(columns=columns)

    missing = PRESSURE_REQUIRED_COLUMNS.difference(pressure.columns)
    if missing:
        raise ValueError(
            f"Pressão assistencial sem colunas obrigatórias: {sorted(missing)}"
        )

    out = pressure.copy()
    out["codigo_ibge"] = _ibge(out["codigo_ibge"])
    out["reference_week"] = pd.to_numeric(
        out["reference_week"], errors="raise"
    ).astype(int)

    if out["codigo_ibge"].duplicated().any():
        raise ValueError("Mais de uma linha de pressão assistencial por município.")
    if not out["reference_week"].eq(int(stable_week)).all():
        raise ValueError(
            "Pressão assistencial deve ter reference_week igual à stable_week."
        )
    if "pressure_evidence" not in out.columns:
        out["pressure_evidence"] = pd.NA

    allowed_validation = {"validated", "under_review", "blocked"}
    invalid = set(out["validation_status"].astype("string")) - allowed_validation
    if invalid:
        raise ValueError(
            f"validation_status de pressão assistencial inválido: {sorted(invalid)}"
        )

    return out[columns]


def build_territorial_intelligence(
    combined_signals: pd.DataFrame,
    confidence: pd.DataFrame,
    silence: pd.DataFrame,
    stable_week: int,
    virology_municipal_weekly: pd.DataFrame | None = None,
    healthcare_pressure: pd.DataFrame | None = None,
    virology_window_weeks: int = 2,
    excluded_dominant_agents: Iterable[str] = (
        "Sem agente detectado/codificado",
        "Detectável sem agente codificado",
    ),
) -> pd.DataFrame:
    required_signal = {
        "codigo_ibge",
        "municipio",
        "SE",
        "signal_status",
        "anomaly_status",
        "trend_status",
        "trend_ratio",
        "trend_log2",
        "observed_value",
        "baseline_median",
    }
    missing = required_signal.difference(combined_signals.columns)
    if missing:
        raise ValueError(f"combined_signals sem colunas: {sorted(missing)}")
    if "signal_confidence" not in confidence.columns:
        raise ValueError("confidence sem signal_confidence.")
    if "silence_status" not in silence.columns:
        raise ValueError("silence sem silence_status.")

    base = combined_signals.loc[
        pd.to_numeric(combined_signals["SE"], errors="coerce").eq(int(stable_week))
    ].copy()
    if base.empty:
        raise ValueError(f"Sem combined_signals para stable_week={stable_week}.")
    base["codigo_ibge"] = _ibge(base["codigo_ibge"])
    if base["codigo_ibge"].duplicated().any():
        raise ValueError("combined_signals possui duplicidade municipal na stable_week.")

    conf = confidence.copy()
    conf["codigo_ibge"] = _ibge(conf["codigo_ibge"])
    sil = silence.copy()
    sil["codigo_ibge"] = _ibge(sil["codigo_ibge"])

    conf_cols = [
        "codigo_ibge",
        "signal_confidence",
        "confidence_model_status",
        "risk_separation",
    ]
    sil_cols = [
        "codigo_ibge",
        "silence_status",
        "silence_model_status",
    ]
    out = base.merge(conf[conf_cols], on="codigo_ibge", how="left", validate="one_to_one")
    out = out.merge(sil[sil_cols], on="codigo_ibge", how="left", validate="one_to_one")

    virology = summarize_virology_window(
        virology_municipal_weekly,
        stable_week=stable_week,
        window_weeks=virology_window_weeks,
        excluded_dominant_agents=excluded_dominant_agents,
    )
    if not virology.empty:
        out = out.merge(virology, on="codigo_ibge", how="left", validate="one_to_one")
    else:
        for col in summarize_virology_window(None, stable_week).columns:
            if col != "codigo_ibge":
                out[col] = pd.NA
        out["virology_status"] = "not_available"

    pressure = validate_healthcare_pressure(healthcare_pressure, stable_week)
    if not pressure.empty:
        out = out.merge(pressure, on="codigo_ibge", how="left", validate="one_to_one")
        out["healthcare_pressure_available"] = out["pressure_status"].notna()
    else:
        out["reference_week"] = int(stable_week)
        out["pressure_status"] = pd.NA
        out["validation_status"] = "not_available"
        out["source_scope"] = "institutional_optional"
        out["pressure_evidence"] = pd.NA
        out["healthcare_pressure_available"] = False

    out["territorial_model_status"] = "under_calibration"
    out["composite_score"] = pd.NA
    out["operational_alert"] = False
    out["validated_for_operational_alert"] = False

    return out.sort_values("codigo_ibge").reset_index(drop=True)
