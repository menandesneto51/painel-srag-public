# -*- coding: utf-8 -*-
from __future__ import annotations

import pandas as pd

from src.operational_review import build_operational_review_queue


def validate_candidate_operational_config(config: dict) -> None:
    principles = config.get("principles") or {}
    required_true = {
        "queue_is_not_risk_rank",
        "human_review_required",
        "patient_level_decisions_disabled",
    }
    for key in required_true:
        if principles.get(key) is not True:
            raise ValueError(f"Config candidata deve manter {key}=true.")

    if principles.get("no_automatic_action") is not True:
        raise ValueError("Config candidata deve manter no_automatic_action=true.")
    if principles.get("composite_score_enabled") is not False:
        raise ValueError("Config candidata deve manter composite_score_enabled=false.")

    rules = config.get("queue_rules") or []
    if not rules:
        raise ValueError("Config candidata sem queue_rules.")

    fallback = rules[-1]
    if fallback.get("queue") != "routine_monitoring":
        raise ValueError(
            "Última regra candidata deve permanecer como fallback routine_monitoring."
        )
    if fallback.get("requires_all_tags") or fallback.get("requires_any_tags"):
        raise ValueError("Fallback routine_monitoring não deve possuir gatilhos.")


def build_candidate_review_queue(
    review_cards: pd.DataFrame,
    candidate_config: dict,
    proposal_id: str,
    candidate_rule_version: str,
    required_municipalities: int = 142,
) -> pd.DataFrame:
    if not str(proposal_id).strip():
        raise ValueError("proposal_id é obrigatório.")
    if not str(candidate_rule_version).strip():
        raise ValueError("candidate_rule_version é obrigatório.")

    validate_candidate_operational_config(candidate_config)

    queue = build_operational_review_queue(
        review_cards,
        candidate_config,
    ).copy()

    if len(queue) != required_municipalities:
        raise ValueError(
            f"Fila candidata deve conter {required_municipalities} municípios; "
            f"recebido {len(queue)}."
        )
    if queue["codigo_ibge"].nunique() != required_municipalities:
        raise ValueError("Fila candidata não possui códigos IBGE únicos completos.")

    if not queue["human_review_required"].astype(bool).all():
        raise ValueError("Fila candidata contém linha sem revisão humana obrigatória.")
    if queue["automatic_execution_enabled"].astype(bool).any():
        raise ValueError("Fila candidata contém execução automática habilitada.")
    if queue["patient_level_decision_enabled"].astype(bool).any():
        raise ValueError("Fila candidata contém decisão em nível de paciente.")
    if queue["composite_score_used"].astype(bool).any():
        raise ValueError("Fila candidata contém score composto.")
    if not queue["queue_is_not_risk_rank"].astype(bool).all():
        raise ValueError("Fila candidata permite interpretação como ranking de risco.")

    queue["proposal_id"] = str(proposal_id)
    queue["candidate_rule_version"] = str(candidate_rule_version)
    queue["candidate_only"] = True
    queue["shadow_only"] = True
    queue["automatic_activation_enabled"] = False
    queue["automatic_rule_change_enabled"] = False

    return queue.sort_values("codigo_ibge").reset_index(drop=True)
