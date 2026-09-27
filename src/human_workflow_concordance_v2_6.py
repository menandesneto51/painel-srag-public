# -*- coding: utf-8 -*-
from __future__ import annotations

import json
from pathlib import Path

import pandas as pd


def load_concordance_config(path: Path) -> dict:
    cfg = json.loads(path.read_text(encoding="utf-8"))
    principles = cfg.get("principles") or {}
    required_true = {
        "human_decision_is_workflow_authority",
        "human_decision_is_not_epidemiological_gold_standard",
        "no_reviewer_scoring",
        "no_municipality_ranking",
        "discordance_triggers_rule_review",
    }
    for key in required_true:
        if principles.get(key) is not True:
            raise ValueError(f"{key} deve ser true.")
    if principles.get("automatic_rule_change") is not False:
        raise ValueError("automatic_rule_change deve ser false.")
    if principles.get("automatic_execution") is not False:
        raise ValueError("automatic_execution deve ser false.")
    return cfg


def classify_workflow_alignment(
    review_queue: str,
    decision_status: str,
    routine_queue: str,
    escalation_decisions: set[str],
    non_escalation_decisions: set[str],
) -> str:
    queue_nonroutine = str(review_queue) != str(routine_queue)
    decision = str(decision_status)

    if decision in escalation_decisions:
        return (
            "nonroutine_escalation_aligned"
            if queue_nonroutine
            else "routine_escalated_rule_review"
        )
    if decision in non_escalation_decisions:
        return (
            "nonroutine_not_escalated_rule_review"
            if queue_nonroutine
            else "routine_non_escalation_aligned"
        )
    return "decision_outside_alignment_map"


def build_human_workflow_concordance(
    decisions: pd.DataFrame,
    config: dict,
    operational_stability: pd.DataFrame | None = None,
    follow_up_status: pd.DataFrame | None = None,
) -> pd.DataFrame:
    required = {
        "decision_record_id",
        "codigo_ibge",
        "municipio",
        "snapshot_id",
        "review_queue",
        "decision_scope",
        "action_id",
        "reviewed_at",
        "reviewer_role",
        "decision_status",
        "decision_recorded_by_human",
        "automatic_execution_enabled",
    }
    missing = required.difference(decisions.columns)
    if missing:
        raise ValueError(f"Decisões v2.5 sem colunas: {sorted(missing)}")
    if not decisions["decision_recorded_by_human"].astype(bool).all():
        raise ValueError("Concordância só aceita decisões humanas validadas.")
    if decisions["automatic_execution_enabled"].astype(bool).any():
        raise ValueError("Decisão com execução automática não pode ser avaliada.")

    routine = config["routine_queue"]
    escalation = set(config["escalation_decisions"])
    non_escalation = set(config["non_escalation_decisions"])

    out = decisions.copy()
    out["workflow_alignment"] = out.apply(
        lambda row: classify_workflow_alignment(
            row["review_queue"],
            row["decision_status"],
            routine,
            escalation,
            non_escalation,
        ),
        axis=1,
    )
    out["rule_review_required"] = out["workflow_alignment"].isin({
        "routine_escalated_rule_review",
        "nonroutine_not_escalated_rule_review",
        "decision_outside_alignment_map",
    })

    if operational_stability is not None and not operational_stability.empty:
        required_stability = {
            "codigo_ibge",
            "workflow_pattern",
            "current_nonroutine_run",
            "current_same_queue_run",
        }
        missing_stability = required_stability.difference(
            operational_stability.columns
        )
        if missing_stability:
            raise ValueError(
                f"Estabilidade v2.4 sem colunas: {sorted(missing_stability)}"
            )
        stability = operational_stability[[
            "codigo_ibge",
            "workflow_pattern",
            "current_nonroutine_run",
            "current_same_queue_run",
        ]].copy()
        stability["codigo_ibge"] = (
            stability["codigo_ibge"].astype("string").str.zfill(7)
        )
        out["codigo_ibge"] = out["codigo_ibge"].astype("string").str.zfill(7)
        out = out.merge(
            stability,
            on="codigo_ibge",
            how="left",
            validate="many_to_one",
        )
    else:
        out["workflow_pattern"] = pd.NA
        out["current_nonroutine_run"] = pd.NA
        out["current_same_queue_run"] = pd.NA

    if follow_up_status is not None and not follow_up_status.empty:
        required_follow = {"decision_record_id", "follow_up_state"}
        missing_follow = required_follow.difference(follow_up_status.columns)
        if missing_follow:
            raise ValueError(
                f"Follow-up v2.5 sem colunas: {sorted(missing_follow)}"
            )
        follow = follow_up_status[[
            "decision_record_id",
            "follow_up_state",
        ]].copy()
        out = out.merge(
            follow,
            on="decision_record_id",
            how="left",
            validate="one_to_one",
        )
    else:
        out["follow_up_state"] = pd.NA

    out["human_decision_is_epidemiological_gold_standard"] = False
    out["reviewer_score_enabled"] = False
    out["municipality_rank_enabled"] = False
    out["automatic_rule_change_enabled"] = False
    out["automatic_execution_enabled"] = False
    out["concordance_status"] = "experimental_rule_governance"

    columns = [
        "decision_record_id",
        "codigo_ibge",
        "municipio",
        "snapshot_id",
        "review_queue",
        "decision_scope",
        "action_id",
        "reviewed_at",
        "reviewer_role",
        "decision_status",
        "workflow_alignment",
        "rule_review_required",
        "workflow_pattern",
        "current_nonroutine_run",
        "current_same_queue_run",
        "follow_up_state",
        "human_decision_is_epidemiological_gold_standard",
        "reviewer_score_enabled",
        "municipality_rank_enabled",
        "automatic_rule_change_enabled",
        "automatic_execution_enabled",
        "concordance_status",
    ]
    return out[columns].sort_values(
        ["workflow_alignment", "reviewed_at", "codigo_ibge"]
    ).reset_index(drop=True)


def summarize_concordance(concordance: pd.DataFrame) -> dict:
    required = {
        "decision_record_id",
        "workflow_alignment",
        "rule_review_required",
        "review_queue",
        "decision_status",
        "reviewer_score_enabled",
        "municipality_rank_enabled",
    }
    missing = required.difference(concordance.columns)
    if missing:
        raise ValueError(f"Concordância sem colunas: {sorted(missing)}")
    if concordance["reviewer_score_enabled"].astype(bool).any():
        raise ValueError("Reviewer score não é permitido.")
    if concordance["municipality_rank_enabled"].astype(bool).any():
        raise ValueError("Ranking municipal não é permitido.")

    return {
        "decision_records": int(len(concordance)),
        "rule_review_records": int(
            concordance["rule_review_required"].astype(bool).sum()
        ),
        "alignment_counts": {
            str(k): int(v)
            for k, v in concordance["workflow_alignment"]
            .astype("string")
            .value_counts(dropna=False)
            .to_dict()
            .items()
        },
        "rule_review_by_queue": {
            str(k): int(v)
            for k, v in concordance.loc[
                concordance["rule_review_required"].astype(bool),
                "review_queue",
            ]
            .astype("string")
            .value_counts(dropna=False)
            .to_dict()
            .items()
        },
        "reviewer_scoring": False,
        "municipality_ranking": False,
        "automatic_rule_change": False,
    }
