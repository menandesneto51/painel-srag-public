# -*- coding: utf-8 -*-
from __future__ import annotations

import re

import pandas as pd


REQUIRED_COLUMNS = {
    "codigo_ibge",
    "reference_week",
    "pressure_status",
    "validation_status",
    "source_scope",
}

OPTIONAL_SAFE_COLUMNS = {
    "pressure_evidence",
    "hospital_occupancy_percent",
    "icu_occupancy_percent",
    "open_requests",
    "pending_transfers",
    "waiting_admission",
    "source_updated_at",
}

PROHIBITED_PATTERNS = (
    r"(^|_)cpf($|_)",
    r"(^|_)cns($|_)",
    r"cartao.*sus",
    r"nome.*paciente",
    r"(^|_)paciente($|_)",
    r"nascimento",
    r"dt_nasc",
    r"telefone",
    r"celular",
    r"endereco",
    r"prontuario",
    r"nome.*mae",
    r"email",
    r"documento",
)


def normalize_column(name: object) -> str:
    value = str(name).strip().lower()
    value = re.sub(r"[^a-z0-9_]+", "_", value)
    return re.sub(r"_+", "_", value).strip("_")


def find_prohibited_columns(columns) -> list[str]:
    hits: list[str] = []
    for original in columns:
        normalized = normalize_column(original)
        if any(re.search(pattern, normalized) for pattern in PROHIBITED_PATTERNS):
            hits.append(str(original))
    return hits


def sanitize_healthcare_pressure(
    frame: pd.DataFrame,
    stable_week: int | None = None,
) -> pd.DataFrame:
    prohibited = find_prohibited_columns(frame.columns)
    if prohibited:
        raise ValueError(
            "Entrada assistencial contém colunas potencialmente identificáveis: "
            + ", ".join(sorted(prohibited))
        )

    normalized_map = {col: normalize_column(col) for col in frame.columns}
    if len(set(normalized_map.values())) != len(normalized_map):
        raise ValueError("Colunas se tornam duplicadas após normalização.")

    data = frame.rename(columns=normalized_map).copy()
    missing = REQUIRED_COLUMNS.difference(data.columns)
    if missing:
        raise ValueError(
            f"Entrada assistencial agregada sem colunas obrigatórias: {sorted(missing)}"
        )

    allowed = REQUIRED_COLUMNS | OPTIONAL_SAFE_COLUMNS
    unexpected = set(data.columns).difference(allowed)
    if unexpected:
        raise ValueError(
            "Entrada assistencial contém colunas fora do contrato agregado: "
            + ", ".join(sorted(unexpected))
        )

    data["codigo_ibge"] = (
        data["codigo_ibge"]
        .astype("string")
        .str.replace(r"\.0$", "", regex=True)
        .str.zfill(7)
    )
    if not data["codigo_ibge"].str.match(r"^51\d{5}$", na=False).all():
        raise ValueError("Há código IBGE inválido ou fora de Mato Grosso.")

    data["reference_week"] = pd.to_numeric(
        data["reference_week"], errors="raise"
    ).astype(int)
    if not data["reference_week"].between(1, 53).all():
        raise ValueError("reference_week deve estar entre 1 e 53.")
    if stable_week is not None and not data["reference_week"].eq(
        int(stable_week)
    ).all():
        raise ValueError(
            "Todas as linhas assistenciais devem usar a mesma stable_week."
        )

    if data["codigo_ibge"].duplicated().any():
        raise ValueError(
            "Entrada assistencial deve conter no máximo uma linha por município."
        )

    allowed_validation = {"validated", "under_review", "blocked"}
    invalid_validation = set(
        data["validation_status"].astype("string").dropna().tolist()
    ).difference(allowed_validation)
    if invalid_validation:
        raise ValueError(
            f"validation_status inválido: {sorted(invalid_validation)}"
        )

    allowed_scope = {"institutional", "public_aggregate"}
    invalid_scope = set(
        data["source_scope"].astype("string").dropna().tolist()
    ).difference(allowed_scope)
    if invalid_scope:
        raise ValueError(f"source_scope inválido: {sorted(invalid_scope)}")

    for col in ("hospital_occupancy_percent", "icu_occupancy_percent"):
        if col in data.columns:
            numeric = pd.to_numeric(data[col], errors="coerce")
            if ((numeric.dropna() < 0) | (numeric.dropna() > 100)).any():
                raise ValueError(f"{col} possui valor fora de 0..100.")
            data[col] = numeric

    for col in ("open_requests", "pending_transfers", "waiting_admission"):
        if col in data.columns:
            numeric = pd.to_numeric(data[col], errors="coerce")
            if (numeric.dropna() < 0).any():
                raise ValueError(f"{col} possui valor negativo.")
            data[col] = numeric

    data["sanitization_status"] = "aggregate_contract_passed"
    data["patient_level_fields_present"] = False
    data["automatic_pressure_classification_enabled"] = False

    ordered = [
        "codigo_ibge",
        "reference_week",
        "pressure_status",
        "validation_status",
        "source_scope",
    ]
    ordered += [c for c in sorted(OPTIONAL_SAFE_COLUMNS) if c in data.columns]
    ordered += [
        "sanitization_status",
        "patient_level_fields_present",
        "automatic_pressure_classification_enabled",
    ]
    return data[ordered].sort_values("codigo_ibge").reset_index(drop=True)
