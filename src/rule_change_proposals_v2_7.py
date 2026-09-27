# -*- coding: utf-8 -*-
from __future__ import annotations

import hashlib

import pandas as pd


REQUIRED_CONCORDANCE_COLUMNS = {
    "decision_record_id",
    "codigo_ibge",
    "municipio",
    "review_queue",
    "decision_status",
    "workflow_alignment",
    "rule_review_required",
}


def _proposal_id(rule_key: str, alignment: str) -> str:
    basis = f"{rule_key}|{alignment}"
    return "prop_" + hashlib.sha256(basis.encode("utf-8")).hexdigest()[:16]


def build_rule_change_proposals(
    concordance: pd.DataFrame,
) -> pd.DataFrame:
    missing = REQUIRED_CONCORDANCE_COLUMNS.difference(concordance.columns)
    if missing:
        raise ValueError(f"Concordância sem colunas: {sorted(missing)}")

    flagged = concordance.loc[
        concordance["rule_review_required"].astype(bool)
    ].copy()
    columns = [
        "proposal_id",
        "rule_key",
        "workflow_alignment",
        "affected_records",
        "affected_municipalities",
        "example_municipalities",
        "proposal_type",
        "proposal_status",
        "problem_statement",
        "analysis_required",
        "automatic_rule_change_enabled",
        "automatic_threshold_change_enabled",
        "proposal_is_not_change",
        "human_approval_required",
    ]
    if flagged.empty:
        return pd.DataFrame(columns=columns)

    rows = []
    for (queue, alignment), group in flagged.groupby(
        ["review_queue", "workflow_alignment"],
        dropna=False,
        sort=True,
    ):
        queue_text = str(queue)
        alignment_text = str(alignment)

        if alignment_text == "routine_escalated_rule_review":
            problem = (
                "A fila de rotina foi seguida por decisão humana de escalonamento. "
                "Revisar se faltou contexto, gatilho ou requisito de evidência."
            )
            proposal_type = "queue_rule"
        elif alignment_text == "nonroutine_not_escalated_rule_review":
            problem = (
                "A fila não rotineira foi seguida por decisão humana sem escalonamento. "
                "Revisar sensibilidade da regra e contexto não modelado."
            )
            proposal_type = "queue_rule"
        else:
            problem = (
                "A decisão humana ficou fora do mapa de concordância atual. "
                "Revisar documentação e cobertura das regras."
            )
            proposal_type = "documentation"

        municipalities = sorted(
            group["municipio"].astype(str).unique().tolist()
        )
        rule_key = f"review_queue::{queue_text}"

        rows.append({
            "proposal_id": _proposal_id(rule_key, alignment_text),
            "rule_key": rule_key,
            "workflow_alignment": alignment_text,
            "affected_records": int(len(group)),
            "affected_municipalities": int(
                group["codigo_ibge"].nunique()
            ),
            "example_municipalities": " | ".join(municipalities[:10]),
            "proposal_type": proposal_type,
            "proposal_status": "draft",
            "problem_statement": problem,
            "analysis_required": (
                "case_review|epidemiology_review|backtest|documentation"
            ),
            "automatic_rule_change_enabled": False,
            "automatic_threshold_change_enabled": False,
            "proposal_is_not_change": True,
            "human_approval_required": True,
        })

    return pd.DataFrame(rows)[columns].sort_values(
        ["proposal_type", "rule_key", "workflow_alignment"]
    ).reset_index(drop=True)


def validate_proposal_registry(
    proposals: pd.DataFrame,
    allowed_statuses: set[str],
    allowed_change_types: set[str],
) -> pd.DataFrame:
    required = {
        "proposal_id",
        "rule_key",
        "proposal_type",
        "proposal_status",
        "problem_statement",
        "automatic_rule_change_enabled",
        "proposal_is_not_change",
        "human_approval_required",
    }
    missing = required.difference(proposals.columns)
    if missing:
        raise ValueError(f"Propostas sem colunas: {sorted(missing)}")

    out = proposals.copy()

    invalid_status = set(out["proposal_status"].astype(str)) - allowed_statuses
    if invalid_status:
        raise ValueError(f"proposal_status inválido: {sorted(invalid_status)}")

    invalid_type = set(out["proposal_type"].astype(str)) - allowed_change_types
    if invalid_type:
        raise ValueError(f"proposal_type inválido: {sorted(invalid_type)}")

    if out["automatic_rule_change_enabled"].astype(bool).any():
        raise ValueError("Proposta não pode habilitar alteração automática.")
    if not out["proposal_is_not_change"].astype(bool).all():
        raise ValueError("Toda proposta deve permanecer distinta de mudança aplicada.")
    if not out["human_approval_required"].astype(bool).all():
        raise ValueError("Toda proposta deve exigir aprovação humana.")
    if out["proposal_id"].duplicated().any():
        raise ValueError("proposal_id duplicado.")

    return out.sort_values("proposal_id").reset_index(drop=True)
