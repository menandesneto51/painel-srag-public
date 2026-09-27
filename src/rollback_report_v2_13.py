# -*- coding: utf-8 -*-
from __future__ import annotations

from datetime import datetime, timezone

import pandas as pd


def build_rollback_summary(
    decisions: pd.DataFrame | None,
    executions: pd.DataFrame | None,
) -> dict:
    summary = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "rollback_decision_records": 0,
        "approved_rollback_decisions": 0,
        "rollback_execution_records": 0,
        "automatic_rollback_enabled": False,
        "automatic_deploy_enabled": False,
        "automatic_rule_change_enabled": False,
        "personal_identifier_storage": False,
    }

    if decisions is not None and not decisions.empty:
        required = {
            "rollback_decision_record_id",
            "rollback_decision",
            "rollback_decision_is_not_rollback_execution",
            "automatic_rollback_enabled",
            "automatic_rule_change_enabled",
        }
        missing = required.difference(decisions.columns)
        if missing:
            raise ValueError(f"Decisões de rollback sem colunas: {sorted(missing)}")
        if decisions["automatic_rollback_enabled"].astype(bool).any():
            raise ValueError("Há decisão com rollback automático habilitado.")
        if decisions["automatic_rule_change_enabled"].astype(bool).any():
            raise ValueError("Há decisão com alteração automática de regra habilitada.")
        if not decisions["rollback_decision_is_not_rollback_execution"].astype(bool).all():
            raise ValueError("Decisão de rollback deve permanecer distinta de execução.")
        summary["rollback_decision_records"] = int(len(decisions))
        summary["approved_rollback_decisions"] = int(
            decisions["rollback_decision"].astype(str).eq("approve_human_rollback").sum()
        )
        summary["decisions_by_state"] = {
            str(k): int(v)
            for k, v in decisions["rollback_decision"]
            .astype("string").value_counts(dropna=False).to_dict().items()
        }

    if executions is not None and not executions.empty:
        required = {
            "rollback_execution_record_id",
            "rollback_execution_state",
            "rollback_record_requires_actual_rollback_evidence",
            "automatic_rollback_enabled",
            "automatic_rule_change_enabled",
        }
        missing = required.difference(executions.columns)
        if missing:
            raise ValueError(f"Execuções de rollback sem colunas: {sorted(missing)}")
        if executions["automatic_rollback_enabled"].astype(bool).any():
            raise ValueError("Há rollback automático habilitado.")
        if executions["automatic_rule_change_enabled"].astype(bool).any():
            raise ValueError("Há alteração automática de regra habilitada.")
        if not executions["rollback_record_requires_actual_rollback_evidence"].astype(bool).all():
            raise ValueError("Execução de rollback deve exigir evidência real.")
        summary["rollback_execution_records"] = int(len(executions))
        summary["executions_by_state"] = {
            str(k): int(v)
            for k, v in executions["rollback_execution_state"]
            .astype("string").value_counts(dropna=False).to_dict().items()
        }

    return summary


def render_rollback_report(summary: dict) -> str:
    lines = [
        "# Relatório Estadual de Rollback — v2.13",
        "",
        "> Governança técnica. Decisão de rollback não é rollback executado; execução exige evidência explícita e verificação humana.",
        "",
        f"- Decisões de rollback: **{summary['rollback_decision_records']}**",
        f"- Decisões aprovadas: **{summary['approved_rollback_decisions']}**",
        f"- Rollbacks com evidência registrada: **{summary['rollback_execution_records']}**",
        "- Rollback automático: **desabilitado**",
        "- Deploy automático: **desabilitado**",
        "- Alteração automática de regra: **desabilitada**",
        "",
    ]
    if "decisions_by_state" in summary:
        lines += ["## Decisões", ""]
        for key, value in sorted(summary["decisions_by_state"].items()):
            lines.append(f"- **{key}**: {value}")
        lines.append("")
    if "executions_by_state" in summary:
        lines += ["## Estados pós-rollback", ""]
        for key, value in sorted(summary["executions_by_state"].items()):
            lines.append(f"- **{key}**: {value}")
        lines.append("")
    lines += [
        "## Governança",
        "",
        "- Um efeito inesperado pós-deploy não prova causalidade epidemiológica.",
        "- Qualquer rollback exige decisão humana explícita.",
        "- O commit restaurado deve ser exatamente o alvo aprovado.",
        "- Nenhuma nova mudança de regra é aplicada automaticamente após rollback.",
        "",
    ]
    return "\n".join(lines)
