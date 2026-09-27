# -*- coding: utf-8 -*-
from __future__ import annotations

from datetime import datetime, timezone

import pandas as pd


def build_postmortem_summary(records: pd.DataFrame | None) -> dict:
    summary = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "records": 0,
        "closed_records": 0,
        "rule_review_reentries": 0,
        "postmortem_is_not_causal_proof": True,
        "learning_is_not_rule_change": True,
        "automatic_rule_change_enabled": False,
        "automatic_issue_creation_enabled": False,
    }

    if records is None or records.empty:
        return summary

    required = {
        "postmortem_record_id",
        "source_record_type",
        "postmortem_status",
        "outcome_state",
        "learning_action_type",
        "reenter_rule_review",
        "postmortem_is_not_causal_proof",
        "learning_is_not_rule_change",
        "automatic_rule_change_enabled",
        "automatic_issue_creation_enabled",
    }
    missing = required.difference(records.columns)
    if missing:
        raise ValueError(
            f"Post-mortem v2.14 sem colunas: {sorted(missing)}"
        )

    if records["automatic_rule_change_enabled"].astype(bool).any():
        raise ValueError("Há mudança automática de regra habilitada.")
    if records["automatic_issue_creation_enabled"].astype(bool).any():
        raise ValueError("Há criação automática de issue habilitada.")
    if not records["postmortem_is_not_causal_proof"].astype(bool).all():
        raise ValueError("Post-mortem deve permanecer não causal.")
    if not records["learning_is_not_rule_change"].astype(bool).all():
        raise ValueError("Aprendizado deve permanecer distinto de mudança.")

    summary["records"] = int(len(records))
    summary["closed_records"] = int(
        records["postmortem_status"].astype(str).eq("closed").sum()
    )
    summary["rule_review_reentries"] = int(
        records["reenter_rule_review"].astype(bool).sum()
    )
    summary["by_source_type"] = {
        str(k): int(v)
        for k, v in records["source_record_type"]
        .astype("string")
        .value_counts(dropna=False)
        .to_dict()
        .items()
    }
    summary["by_outcome_state"] = {
        str(k): int(v)
        for k, v in records["outcome_state"]
        .astype("string")
        .value_counts(dropna=False)
        .to_dict()
        .items()
    }
    summary["by_learning_action"] = {
        str(k): int(v)
        for k, v in records["learning_action_type"]
        .astype("string")
        .value_counts(dropna=False)
        .to_dict()
        .items()
    }
    return summary


def render_postmortem_report(summary: dict) -> str:
    lines = [
        "# Relatório Estadual de Post-Mortem e Aprendizado — v2.14",
        "",
        "> Aprendizado institucional não é prova causal e não altera regras automaticamente.",
        "",
        f"- Registros: **{summary['records']}**",
        f"- Post-mortems fechados: **{summary['closed_records']}**",
        f"- Retornos propostos ao ciclo de regra: **{summary['rule_review_reentries']}**",
        "- Mudança automática de regra: **desabilitada**",
        "- Criação automática de issue: **desabilitada**",
        "",
    ]

    for title, key in (
        ("Fontes", "by_source_type"),
        ("Desfechos do post-mortem", "by_outcome_state"),
        ("Ações de aprendizado", "by_learning_action"),
    ):
        if key in summary:
            lines += [f"## {title}", ""]
            for item, value in sorted(summary[key].items()):
                lines.append(f"- **{item}**: {value}")
            lines.append("")

    lines += [
        "## Governança",
        "",
        "- Fatores contribuintes não devem ser promovidos automaticamente a conclusões causais.",
        "- learning_action_type=rule_review apenas devolve o tema ao fluxo humano de governança.",
        "- Nenhuma regra, threshold, issue, deploy ou rollback é acionado automaticamente.",
        "",
    ]
    return "\n".join(lines)
