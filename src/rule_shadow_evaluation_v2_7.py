# -*- coding: utf-8 -*-
from __future__ import annotations

import pandas as pd

from src.human_workflow_concordance_v2_6 import classify_workflow_alignment


REQUIRED_ASSIGNMENT_COLUMNS = {
    "codigo_ibge",
    "municipio",
    "review_queue",
}


def _normalize_assignments(
    frame: pd.DataFrame,
    label: str,
    required_municipalities: int,
) -> pd.DataFrame:
    missing = REQUIRED_ASSIGNMENT_COLUMNS.difference(frame.columns)
    if missing:
        raise ValueError(
            f"{label} sem colunas obrigatórias: {sorted(missing)}"
        )

    out = frame.copy()
    out["codigo_ibge"] = (
        out["codigo_ibge"]
        .astype("string")
        .str.replace(r"\.0$", "", regex=True)
        .str.zfill(7)
    )
    if not out["codigo_ibge"].str.match(r"^51\d{5}$", na=False).all():
        raise ValueError(f"{label}: código IBGE inválido ou fora de MT.")
    if out["codigo_ibge"].duplicated().any():
        raise ValueError(f"{label}: município duplicado.")
    if len(out) != required_municipalities:
        raise ValueError(
            f"{label}: esperado {required_municipalities} municípios; "
            f"recebido {len(out)}."
        )
    if out["review_queue"].astype("string").str.strip().eq("").any():
        raise ValueError(f"{label}: review_queue vazio.")
    return out[["codigo_ibge", "municipio", "review_queue"]].sort_values(
        "codigo_ibge"
    ).reset_index(drop=True)


def _alignment_group(value: object) -> str:
    text = "" if value is None or pd.isna(value) else str(value)
    if text in {
        "nonroutine_escalation_aligned",
        "routine_non_escalation_aligned",
    }:
        return "aligned"
    if text in {
        "routine_escalated_rule_review",
        "nonroutine_not_escalated_rule_review",
        "decision_outside_alignment_map",
    }:
        return "rule_review"
    return "unmapped"


def compare_shadow_assignments(
    current_assignments: pd.DataFrame,
    candidate_assignments: pd.DataFrame,
    required_municipalities: int = 142,
    decisions: pd.DataFrame | None = None,
    routine_queue: str = "routine_monitoring",
    escalation_decisions: set[str] | None = None,
    non_escalation_decisions: set[str] | None = None,
    proposal_id: str | None = None,
    candidate_rule_version: str | None = None,
) -> pd.DataFrame:
    current = _normalize_assignments(
        current_assignments, "Fila atual", required_municipalities
    ).rename(columns={
        "municipio": "municipio_current",
        "review_queue": "current_review_queue",
    })
    candidate = _normalize_assignments(
        candidate_assignments, "Fila candidata", required_municipalities
    ).rename(columns={
        "municipio": "municipio_candidate",
        "review_queue": "candidate_review_queue",
    })

    if current["codigo_ibge"].tolist() != candidate["codigo_ibge"].tolist():
        raise ValueError("Fila atual e candidata possuem conjuntos territoriais distintos.")

    out = current.merge(
        candidate,
        on="codigo_ibge",
        how="inner",
        validate="one_to_one",
    )
    mismatch_name = (
        out["municipio_current"].astype(str)
        != out["municipio_candidate"].astype(str)
    )
    if mismatch_name.any():
        raise ValueError("Nome municipal divergente entre fila atual e candidata.")

    out["municipio"] = out["municipio_current"]
    out["queue_changed"] = (
        out["current_review_queue"].astype(str)
        != out["candidate_review_queue"].astype(str)
    )
    out["queue_transition"] = (
        out["current_review_queue"].astype(str)
        + " -> "
        + out["candidate_review_queue"].astype(str)
    )

    out["proposal_id"] = proposal_id or ""
    out["candidate_rule_version"] = candidate_rule_version or ""
    out["shadow_only"] = True
    out["automatic_activation_enabled"] = False
    out["automatic_rule_change_enabled"] = False
    out["reviewer_score_enabled"] = False
    out["municipality_rank_enabled"] = False

    if decisions is None or decisions.empty:
        out["decision_record_id"] = pd.NA
        out["decision_status"] = pd.NA
        out["current_alignment"] = pd.NA
        out["candidate_alignment"] = pd.NA
        out["alignment_delta"] = "no_human_decision_context"
        out["human_decision_is_epidemiological_gold_standard"] = False
        return out[[
            "codigo_ibge",
            "municipio",
            "current_review_queue",
            "candidate_review_queue",
            "queue_changed",
            "queue_transition",
            "decision_record_id",
            "decision_status",
            "current_alignment",
            "candidate_alignment",
            "alignment_delta",
            "proposal_id",
            "candidate_rule_version",
            "shadow_only",
            "automatic_activation_enabled",
            "automatic_rule_change_enabled",
            "reviewer_score_enabled",
            "municipality_rank_enabled",
            "human_decision_is_epidemiological_gold_standard",
        ]]

    required_decisions = {
        "decision_record_id",
        "codigo_ibge",
        "decision_status",
    }
    missing = required_decisions.difference(decisions.columns)
    if missing:
        raise ValueError(
            f"Decisões humanas sem colunas: {sorted(missing)}"
        )

    escalation = escalation_decisions or set()
    non_escalation = non_escalation_decisions or set()

    dec = decisions.copy()
    dec["codigo_ibge"] = (
        dec["codigo_ibge"]
        .astype("string")
        .str.replace(r"\.0$", "", regex=True)
        .str.zfill(7)
    )
    # Múltiplas decisões por município são preservadas: a avaliação é por decisão.
    merged = out.merge(
        dec[["decision_record_id", "codigo_ibge", "decision_status"]],
        on="codigo_ibge",
        how="left",
        validate="one_to_many",
    )

    def current_alignment(row) -> str:
        if pd.isna(row["decision_record_id"]):
            return "no_human_decision_context"
        return classify_workflow_alignment(
            row["current_review_queue"],
            row["decision_status"],
            routine_queue,
            escalation,
            non_escalation,
        )

    def candidate_alignment(row) -> str:
        if pd.isna(row["decision_record_id"]):
            return "no_human_decision_context"
        return classify_workflow_alignment(
            row["candidate_review_queue"],
            row["decision_status"],
            routine_queue,
            escalation,
            non_escalation,
        )

    merged["current_alignment"] = merged.apply(current_alignment, axis=1)
    merged["candidate_alignment"] = merged.apply(candidate_alignment, axis=1)

    def delta(row) -> str:
        cur = _alignment_group(row["current_alignment"])
        cand = _alignment_group(row["candidate_alignment"])
        if cur == "rule_review" and cand == "aligned":
            return "workflow_agreement_improved"
        if cur == "aligned" and cand == "rule_review":
            return "workflow_agreement_worsened"
        if cur == "aligned" and cand == "aligned":
            return "workflow_agreement_remains_aligned"
        if cur == "rule_review" and cand == "rule_review":
            return "workflow_agreement_remains_rule_review"
        if cur == "unmapped" or cand == "unmapped":
            return "workflow_agreement_unmapped"
        return "no_human_decision_context"

    merged["alignment_delta"] = merged.apply(delta, axis=1)
    merged["human_decision_is_epidemiological_gold_standard"] = False

    columns = [
        "codigo_ibge",
        "municipio",
        "current_review_queue",
        "candidate_review_queue",
        "queue_changed",
        "queue_transition",
        "decision_record_id",
        "decision_status",
        "current_alignment",
        "candidate_alignment",
        "alignment_delta",
        "proposal_id",
        "candidate_rule_version",
        "shadow_only",
        "automatic_activation_enabled",
        "automatic_rule_change_enabled",
        "reviewer_score_enabled",
        "municipality_rank_enabled",
        "human_decision_is_epidemiological_gold_standard",
    ]
    return merged[columns].sort_values(
        ["codigo_ibge", "decision_record_id"],
        na_position="last",
    ).reset_index(drop=True)


def summarize_shadow_evaluation(shadow: pd.DataFrame) -> dict:
    required = {
        "codigo_ibge",
        "queue_changed",
        "alignment_delta",
        "shadow_only",
        "automatic_activation_enabled",
        "reviewer_score_enabled",
        "municipality_rank_enabled",
    }
    missing = required.difference(shadow.columns)
    if missing:
        raise ValueError(f"Shadow evaluation sem colunas: {sorted(missing)}")
    if not shadow["shadow_only"].astype(bool).all():
        raise ValueError("Toda avaliação v2.7 deve permanecer em shadow_only.")
    if shadow["automatic_activation_enabled"].astype(bool).any():
        raise ValueError("Ativação automática não é permitida.")
    if shadow["reviewer_score_enabled"].astype(bool).any():
        raise ValueError("Reviewer scoring não é permitido.")
    if shadow["municipality_rank_enabled"].astype(bool).any():
        raise ValueError("Ranking municipal não é permitido.")

    municipality_view = shadow.drop_duplicates("codigo_ibge")
    return {
        "rows": int(len(shadow)),
        "municipalities": int(shadow["codigo_ibge"].nunique()),
        "municipalities_with_queue_change": int(
            municipality_view["queue_changed"].astype(bool).sum()
        ),
        "queue_change_fraction": (
            float(municipality_view["queue_changed"].astype(bool).mean())
            if len(municipality_view) else 0.0
        ),
        "alignment_delta_counts": {
            str(k): int(v)
            for k, v in shadow["alignment_delta"]
            .astype("string")
            .value_counts(dropna=False)
            .to_dict()
            .items()
        },
        "shadow_only": True,
        "automatic_activation": False,
        "automatic_rule_change": False,
        "reviewer_scoring": False,
        "municipality_ranking": False,
        "human_decision_is_epidemiological_gold_standard": False,
    }
