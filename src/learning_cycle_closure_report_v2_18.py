# -*- coding: utf-8 -*-
from __future__ import annotations

from datetime import datetime, timezone

import pandas as pd


def build_learning_cycle_closure_summary(
    records: pd.DataFrame | None,
) -> dict:
    summary = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "records": 0,
        "learning_cycle_closed_human": 0,
        "learning_cycle_open": 0,
        "learning_cycle_closure_deferred": 0,
        "postmortem_closed_is_not_learning_cycle_closed": True,
        "closure_is_not_epidemiological_effect": True,
        "automatic_closure_enabled": False,
        "automatic_issue_creation_enabled": False,
        "automatic_rule_change_enabled": False,
    }
    if records is None or records.empty:
        return summary

    required = {
        "learning_closure_record_id",
        "learning_cycle_state",
        "all_actions_terminal",
        "postmortem_closed_is_not_learning_cycle_closed",
        "closure_is_not_epidemiological_effect",
        "automatic_closure_enabled",
        "automatic_issue_creation_enabled",
        "automatic_rule_change_enabled",
    }
    missing = required.difference(records.columns)
    if missing:
        raise ValueError(f"Fechamento v2.18 sem colunas: {sorted(missing)}")

    if not records[
        "postmortem_closed_is_not_learning_cycle_closed"
    ].astype(bool).all():
        raise ValueError("Fechamento documental não pode equivaler ao ciclo de aprendizado.")
    if not records["closure_is_not_epidemiological_effect"].astype(bool).all():
        raise ValueError("Fechamento não pode equivaler a efeito epidemiológico.")
    for col in (
        "automatic_closure_enabled",
        "automatic_issue_creation_enabled",
        "automatic_rule_change_enabled",
    ):
        if records[col].astype(bool).any():
            raise ValueError(f"{col} deve permanecer false.")

    summary["records"] = int(len(records))
    counts = records["learning_cycle_state"].astype(str).value_counts()
    for key in (
        "learning_cycle_closed_human",
        "learning_cycle_open",
        "learning_cycle_closure_deferred",
    ):
        summary[key] = int(counts.get(key, 0))
    summary["by_learning_action_type"] = {
        str(k): int(v)
        for k, v in records["learning_action_type"]
        .astype("string")
        .value_counts(dropna=False)
        .to_dict()
        .items()
    }
    return summary


def render_learning_cycle_closure_report(summary: dict) -> str:
    lines = [
        "# Relatório de Encerramento do Ciclo de Aprendizado — v2.18",
        "",
        "> Post-mortem fechado não significa ciclo de aprendizado encerrado. Encerramento não é evidência de efeito epidemiológico.",
        "",
        f"- Registros: **{summary['records']}**",
        f"- Ciclos fechados por decisão humana: **{summary['learning_cycle_closed_human']}**",
        f"- Ciclos mantidos abertos: **{summary['learning_cycle_open']}**",
        f"- Fechamentos adiados: **{summary['learning_cycle_closure_deferred']}**",
        "- Fechamento automático: **desabilitado**",
        "- Criação automática de issue: **desabilitada**",
        "- Mudança automática de regra: **desabilitada**",
        "",
        "## Governança",
        "",
        "- close_learning_cycle exige ações v2.17 terminais e revisões humanas aprovadas.",
        "- rule_review exige handoff de governança presente e revisado.",
        "- o registro v2.18 não altera os artefatos de origem.",
        "- o fechamento não prova efetividade nem causalidade epidemiológica.",
        "",
    ]
    return "\n".join(lines)
