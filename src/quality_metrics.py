# -*- coding: utf-8 -*-
from __future__ import annotations

import json
from pathlib import Path

import pandas as pd

from src.sivep_pipeline import detect_text_format, digits, municipality_reference


def parse_date(series: pd.Series) -> pd.Series:
    return pd.to_datetime(series, dayfirst=True, errors="coerce")


def _safe_median_days(series: pd.Series) -> float | None:
    values = pd.to_numeric(series, errors="coerce").dropna()
    if values.empty:
        return None
    return float(values.median())


def _safe_percent(numerator: int, denominator: int) -> float | None:
    if denominator <= 0:
        return None
    return float(numerator / denominator * 100.0)


def build_quality_metrics(
    sivep_path: Path,
    population_path: Path,
    config_path: Path,
    chunksize: int = 100_000,
) -> tuple[pd.DataFrame, dict]:
    cfg = json.loads(config_path.read_text(encoding="utf-8"))
    territory = cfg["territorial_scope"]
    time_cfg = cfg["time"]
    severity = cfg["severity"]
    quality = cfg["quality"]

    uf_field = territory["residence_uf_field"]
    mun_field = territory["municipality_code_candidates"][0]
    symptom_date_field = time_cfg["symptom_date_field"]
    outcome_field = severity["outcome_field"]

    notification_field = quality["notification_date_field"]
    digitization_field = quality["digitization_date_field"]
    closure_field = quality["closure_date_field"]
    classification_field = quality["final_classification_field"]

    required = [
        uf_field,
        mun_field,
        symptom_date_field,
        notification_field,
        digitization_field,
        closure_field,
        classification_field,
        outcome_field,
    ]

    encoding, sep = detect_text_format(sivep_path)
    header = pd.read_csv(sivep_path, sep=sep, encoding=encoding, nrows=0)
    missing = [field for field in required if field not in header.columns]
    if missing:
        raise ValueError(f"Banco SIVEP sem campos de qualidade obrigatórios: {missing}")

    ref = municipality_reference(population_path)
    ref6 = set(ref["codigo_sivep_6"].tolist())

    parts: list[pd.DataFrame] = []
    total_mt = 0
    excluded_invalid_municipality = 0

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
        total_mt += len(chunk)
        if chunk.empty:
            continue

        chunk["codigo_sivep_6"] = chunk[mun_field].map(digits).str[:6]
        valid_mun = chunk["codigo_sivep_6"].isin(ref6)
        excluded_invalid_municipality += int((~valid_mun).sum())
        chunk = chunk.loc[valid_mun].copy()
        if chunk.empty:
            continue

        symptom = parse_date(chunk[symptom_date_field])
        notification = parse_date(chunk[notification_field])
        digitization = parse_date(chunk[digitization_field])
        closure = parse_date(chunk[closure_field])

        chunk["notification_delay_days"] = (notification - symptom).dt.days
        chunk["digitization_delay_days"] = (digitization - notification).dt.days

        outcome = chunk[outcome_field].astype("string").str.strip()
        classification = chunk[classification_field].astype("string").str.strip()

        chunk["outcome_complete"] = outcome.isin(["1", "2", "3"]).astype(int)
        chunk["classified"] = (
            classification.notna()
            & classification.ne("")
            & classification.ne("9")
        ).astype(int)
        chunk["closure_complete"] = (
            chunk["classified"].eq(1) & closure.notna()
        ).astype(int)

        chunk["negative_notification_delay"] = (
            chunk["notification_delay_days"].notna()
            & chunk["notification_delay_days"].lt(0)
        ).astype(int)
        chunk["negative_digitization_delay"] = (
            chunk["digitization_delay_days"].notna()
            & chunk["digitization_delay_days"].lt(0)
        ).astype(int)
        chunk["closure_before_notification"] = (
            closure.notna() & notification.notna() & closure.lt(notification)
        ).astype(int)
        chunk["digitization_before_notification"] = (
            digitization.notna() & notification.notna() & digitization.lt(notification)
        ).astype(int)

        parts.append(chunk[[
            "codigo_sivep_6",
            "notification_delay_days",
            "digitization_delay_days",
            "outcome_complete",
            "classified",
            "closure_complete",
            "negative_notification_delay",
            "negative_digitization_delay",
            "closure_before_notification",
            "digitization_before_notification",
        ]])

    base = ref[[
        "codigo_ibge",
        "codigo_sivep_6",
        "municipio",
        "populacao",
    ]].copy()

    if parts:
        records = pd.concat(parts, ignore_index=True)
    else:
        records = pd.DataFrame(columns=[
            "codigo_sivep_6",
            "notification_delay_days",
            "digitization_delay_days",
            "outcome_complete",
            "classified",
            "closure_complete",
            "negative_notification_delay",
            "negative_digitization_delay",
            "closure_before_notification",
            "digitization_before_notification",
        ])

    rows = []
    for ref_row in base.itertuples(index=False):
        sub = records.loc[records["codigo_sivep_6"] == ref_row.codigo_sivep_6]
        n = int(len(sub))
        valid_notification_delay = pd.to_numeric(
            sub["notification_delay_days"], errors="coerce"
        )
        valid_notification_delay = valid_notification_delay.loc[
            valid_notification_delay.ge(0)
        ]
        valid_digitization_delay = pd.to_numeric(
            sub["digitization_delay_days"], errors="coerce"
        )
        valid_digitization_delay = valid_digitization_delay.loc[
            valid_digitization_delay.ge(0)
        ]

        outcome_complete = int(sub["outcome_complete"].sum()) if n else 0
        classified = int(sub["classified"].sum()) if n else 0
        closure_complete = int(sub["closure_complete"].sum()) if n else 0

        temporal_errors = 0
        if n:
            temporal_errors = int(
                sub[[
                    "negative_notification_delay",
                    "negative_digitization_delay",
                    "closure_before_notification",
                    "digitization_before_notification",
                ]].max(axis=1).sum()
            )

        rows.append({
            "codigo_ibge": ref_row.codigo_ibge,
            "municipio": ref_row.municipio,
            "populacao": int(ref_row.populacao),
            "registros": n,
            "atraso_notificacao_mediana_dias": _safe_median_days(valid_notification_delay),
            "atraso_digitacao_mediana_dias": _safe_median_days(valid_digitization_delay),
            "desfecho_completo_percent": _safe_percent(outcome_complete, n),
            "encerramento_completo_percent": _safe_percent(closure_complete, classified),
            "registros_classificados": classified,
            "inconsistencias_temporais": temporal_errors,
            "inconsistencia_temporal_percent": _safe_percent(temporal_errors, n),
            "quality_status": "observed" if n > 0 else "insufficient_data",
        })

    municipal = pd.DataFrame(rows)
    if len(municipal) != 142:
        raise ValueError(f"Esperados 142 municípios; encontrados {len(municipal)}.")
    if municipal["codigo_ibge"].duplicated().any():
        raise ValueError("Códigos IBGE duplicados na camada de qualidade.")

    metadata = {
        "dimension": "surveillance_quality",
        "risk_separation": True,
        "municipality_count": 142,
        "mt_records_seen": int(total_mt),
        "excluded_invalid_municipality": int(excluded_invalid_municipality),
        "metrics": [
            "atraso_notificacao_mediana_dias",
            "atraso_digitacao_mediana_dias",
            "desfecho_completo_percent",
            "encerramento_completo_percent",
            "inconsistencia_temporal_percent",
        ],
        "interpretation": (
            "Qualidade/oportunidade não compõe automaticamente o risco epidemiológico. "
            "Usar para confiança do sinal, investigação de dados e gestão da vigilância."
        ),
    }
    return municipal, metadata
