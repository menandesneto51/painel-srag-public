# -*- coding: utf-8 -*-
from __future__ import annotations

from datetime import datetime, timezone

import pandas as pd


def build_learning_action_followup_summary(
    records: pd.DataFrame | None,
) -> dict:
    summary = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "actions": 0,
        "overdue": 0,
        "verified_closed": 0,
        "verification_rejected": 0,
        "blocked": 0,
        "tracking_is_not_execution": True,
        "completion_is_not_effectiveness_proof": True,
        "verification_is_not_epidemiological_effect": True,
        "overdue_is_not_risk": True,
        "automatic_execution_enabled": False,
        "automatic_issue_creation_enabled": False,
        "automatic_rule_change_enabled": False,
    }

    if records is None or records.empty:
        return summary

    required = {
        "learning_action_record_id",
        "learning_action_type",
        "action_status",
        "verification_status",
        "follow_up_state",
        "overdue",
        "tracking_is_not_execution",
        "completion_is_not_effectiveness_proof",
        "verification_is_not_epidemiological_effect",
        "overdue_is_not_risk",
        "automatic_execution_enabled",
        "automatic_issue_creation_enabled",
        "automatic_rule_change_enabled",
    }
    missing = required.difference(records.columns)
    if missing:
        raise ValueError(
            f"Follow-up v2.17 sem colunas: {sorted(missing)}"
        )

    for col in (
        "tracking_is_not_execution",
        "completion_is_not_effectiveness_proof",
        "verification_is_not_epidemiological_effect",
        "overdue_is_not_risk",
    ):
        if not records[col].astype(bool).all():
            raise ValueError(f"{col} deve permanecer true.")

    for col in (
        "automatic_execution_enabled",
        "automatic_issue_creation_enabled",
        "automatic_rule_change_enabled",
    ):
        if records[col].astype(bool).any():
            raise ValueError(f"{col} deve permanecer false.")

    summary["actions"] = int(len(records))
    summary["overdue"] = int(records["overdue"].astype(bool).sum())
    summary["verified_closed"] = int(
        records["follow_up_state"].astype(str).eq("verified_closed").sum()
    )
    summary["verification_rejected"] = int(
        records["follow_up_state"].astype(str).eq("verification_rejected").sum()
    )
    summary["blocked"] = int(
        records["follow_up_state"]
        .astype(str)
        .isin({"blocked", "blocked_overdue"})
        .sum()
    )
    summary["by_action_type"] = {
        str(k): int(v)
        for k, v in records["learning_action_type"]
        .astype("string")
        .value_counts(dropna=False)
        .to_dict()
        .items()
    }
    summary["by_follow_up_state"] = {
        str(k): int(v)
        for k, v in records["follow_up_state"]
        .astype("string")
        .value_counts(dropna=False)
        .to_dict()
        .items()
    }
    return summary


def render_learning_action_followup_report(summary: dict) -> str:
    lines = [
        "# Relatório de Follow-up das Ações de Aprendizado — v2.17",
        "",
        "> Conclusão de ação não é prova de efetividade epidemiológica. Fechamento verificado exige evidência e revisão humana.",
        "",
        f"- Ações: **{summary['actions']}**",
        f"- Atrasadas: **{summary['overdue']}**",
        f"- Fechadas com verificação humana: **{summary['verified_closed']}**",
        f"- Verificação rejeitada: **{summary['verification_rejected']}**",
        f"- Bloqueadas: **{summary['blocked']}**",
        "- Execução automática: **desabilitada**",
        "- Criação automática de issue: **desabilitada**",
        "- Mudança automática de regra: **desabilitada**",
        "",
    ]

    for title, key in (
        ("Tipos de ação", "by_action_type"),
        ("Estados de follow-up", "by_follow_up_state"),
    ):
        if key in summary:
            lines += [f"## {title}", ""]
            for item, value in sorted(summary[key].items()):
                lines.append(f"- **{item}**: {value}")
            lines.append("")

    lines += [
        "## Governança",
        "",
        "- overdue representa atraso de workflow, não risco epidemiológico.",
        "- completed registra conclusão declarada e evidenciada, não efetividade.",
        "- verified_closed registra verificação humana da evidência, não efeito causal.",
        "- ações rule_review concluídas exigem handoff explícito para governança.",
        "- nenhuma issue, regra, threshold, deploy ou rollback é criado automaticamente.",
        "",
    ]
    return "\n".join(lines)
