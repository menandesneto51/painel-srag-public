# -*- coding: utf-8 -*-
from __future__ import annotations

from datetime import datetime

import pandas as pd


ALLOWED_DECISIONS = {
    "continue_monitoring",
    "request_data_validation",
    "request_epi_investigation",
    "request_laboratory_review",
    "request_assistance_coordination",
    "request_multidisciplinary_review",
    "closed_no_escalation",
}

REQUIRED_COLUMNS = {
    "codigo_ibge",
    "municipio",
    "review_queue",
    "reviewed_at",
    "reviewer_role",
    "decision_status",
    "rationale",
}


def validate_review_decisions(frame: pd.DataFrame) -> pd.DataFrame:
    missing = REQUIRED_COLUMNS.difference(frame.columns)
    if missing:
        raise ValueError(
            f"Registro de decisão humana sem colunas obrigatórias: {sorted(missing)}"
        )

    data = frame.copy()
    data["codigo_ibge"] = (
        data["codigo_ibge"]
        .astype("string")
        .str.replace(r"\.0$", "", regex=True)
        .str.zfill(7)
    )
    if not data["codigo_ibge"].str.match(r"^51\d{5}$", na=False).all():
        raise ValueError("Há código IBGE inválido ou fora de Mato Grosso.")

    decision = data["decision_status"].astype("string")
    invalid = set(decision.dropna().tolist()).difference(ALLOWED_DECISIONS)
    if invalid:
        raise ValueError(f"decision_status inválido: {sorted(invalid)}")

    for col in ("reviewer_role", "rationale", "review_queue"):
        if data[col].astype("string").str.strip().eq("").any():
            raise ValueError(f"{col} não pode ser vazio.")

    parsed = pd.to_datetime(data["reviewed_at"], errors="coerce", utc=True)
    if parsed.isna().any():
        raise ValueError("reviewed_at contém data/hora inválida.")
    data["reviewed_at"] = parsed.astype("string")

    if data.duplicated(["codigo_ibge", "reviewed_at", "decision_status"]).any():
        raise ValueError("Há decisão humana duplicada para o mesmo município/momento/status.")

    # Workflow only: never infer or execute the requested action.
    data["decision_recorded_by_human"] = True
    data["automatic_execution_enabled"] = False
    data["patient_level_decision_enabled"] = False
    data["decision_log_status"] = "human_review_audit_record"

    safe_optional = [
        "reviewer_role",
        "evidence_refs",
        "notes",
    ]
    ordered = [
        "codigo_ibge",
        "municipio",
        "review_queue",
        "reviewed_at",
        "reviewer_role",
        "decision_status",
        "rationale",
    ]
    ordered += [c for c in safe_optional if c in data.columns and c not in ordered]
    ordered += [
        "decision_recorded_by_human",
        "automatic_execution_enabled",
        "patient_level_decision_enabled",
        "decision_log_status",
    ]
    return data[ordered].sort_values(
        ["reviewed_at", "codigo_ibge"]
    ).reset_index(drop=True)
