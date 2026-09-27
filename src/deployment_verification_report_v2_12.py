# -*- coding: utf-8 -*-
from __future__ import annotations

from datetime import datetime, timezone

import pandas as pd


def build_deployment_verification_summary(
    deploy_decisions: pd.DataFrame | None,
    deployments: pd.DataFrame | None,
    effects: pd.DataFrame | None,
) -> dict:
    summary = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "deploy_decision_records": 0,
        "approved_deploy_decisions": 0,
        "deployment_records": 0,
        "effect_verification_records": 0,
        "automatic_deploy_enabled": False,
        "automatic_rollback_enabled": False,
        "automatic_rule_change_enabled": False,
        "effect_verification_is_not_causal_inference": True,
        "personal_identifier_storage": False,
    }

    if deploy_decisions is not None and not deploy_decisions.empty:
        required = {
            "deploy_decision_record_id",
            "deploy_decision",
            "deploy_decision_is_not_deploy_execution",
            "automatic_deploy_enabled",
            "automatic_rollback_enabled",
        }
        missing = required.difference(deploy_decisions.columns)
        if missing:
            raise ValueError(
                f"Decisões de deploy sem colunas: {sorted(missing)}"
            )
        if deploy_decisions["automatic_deploy_enabled"].astype(bool).any():
            raise ValueError("Há decisão com deploy automático habilitado.")
        if deploy_decisions["automatic_rollback_enabled"].astype(bool).any():
            raise ValueError("Há decisão com rollback automático habilitado.")
        if not deploy_decisions[
            "deploy_decision_is_not_deploy_execution"
        ].astype(bool).all():
            raise ValueError(
                "Decisão de deploy deve permanecer distinta de execução."
            )

        summary["deploy_decision_records"] = int(len(deploy_decisions))
        summary["approved_deploy_decisions"] = int(
            deploy_decisions["deploy_decision"]
            .astype(str)
            .eq("approve_human_deploy")
            .sum()
        )
        summary["deploy_decisions_by_state"] = {
            str(k): int(v)
            for k, v in deploy_decisions["deploy_decision"]
            .astype("string")
            .value_counts(dropna=False)
            .to_dict()
            .items()
        }

    if deployments is not None and not deployments.empty:
        required = {
            "deployment_record_id",
            "deployment_state",
            "deployment_record_requires_actual_deploy_evidence",
            "deployment_is_not_effect_verification",
            "automatic_deploy_enabled",
            "automatic_rollback_enabled",
        }
        missing = required.difference(deployments.columns)
        if missing:
            raise ValueError(
                f"Registros de deploy sem colunas: {sorted(missing)}"
            )
        if deployments["automatic_deploy_enabled"].astype(bool).any():
            raise ValueError("Há deploy com automação habilitada.")
        if deployments["automatic_rollback_enabled"].astype(bool).any():
            raise ValueError("Há deploy com rollback automático habilitado.")
        if not deployments[
            "deployment_record_requires_actual_deploy_evidence"
        ].astype(bool).all():
            raise ValueError("Registro de deploy exige evidência real.")
        if not deployments[
            "deployment_is_not_effect_verification"
        ].astype(bool).all():
            raise ValueError(
                "Deploy deve permanecer distinto de verificação de efeito."
            )

        summary["deployment_records"] = int(len(deployments))
        summary["deployments_by_state"] = {
            str(k): int(v)
            for k, v in deployments["deployment_state"]
            .astype("string")
            .value_counts(dropna=False)
            .to_dict()
            .items()
        }

    if effects is not None and not effects.empty:
        required = {
            "effect_verification_record_id",
            "effect_state",
            "effect_verification_is_not_causal_inference",
            "automatic_rule_change_enabled",
            "automatic_rollback_enabled",
        }
        missing = required.difference(effects.columns)
        if missing:
            raise ValueError(
                f"Verificação de efeito sem colunas: {sorted(missing)}"
            )
        if effects["automatic_rule_change_enabled"].astype(bool).any():
            raise ValueError("Há alteração automática de regra habilitada.")
        if effects["automatic_rollback_enabled"].astype(bool).any():
            raise ValueError("Há rollback automático habilitado.")
        if not effects[
            "effect_verification_is_not_causal_inference"
        ].astype(bool).all():
            raise ValueError(
                "Verificação de efeito deve permanecer não causal."
            )

        summary["effect_verification_records"] = int(len(effects))
        summary["effects_by_state"] = {
            str(k): int(v)
            for k, v in effects["effect_state"]
            .astype("string")
            .value_counts(dropna=False)
            .to_dict()
            .items()
        }

    return summary


def render_deployment_verification_markdown(summary: dict) -> str:
    lines = [
        "# Relatório Estadual de Deploy e Verificação — v2.12",
        "",
        "> Registro de governança técnica. Decisão de deploy não é deploy executado; deploy não é verificação de efeito; verificação de efeito não é inferência causal epidemiológica.",
        "",
        f"- Decisões de deploy: **{summary['deploy_decision_records']}**",
        f"- Decisões aprovadas para deploy humano: **{summary['approved_deploy_decisions']}**",
        f"- Deploys com evidência registrada: **{summary['deployment_records']}**",
        f"- Verificações de efeito: **{summary['effect_verification_records']}**",
        "- Deploy automático: **desabilitado**",
        "- Rollback automático: **desabilitado**",
        "- Alteração automática de regra: **desabilitada**",
        "",
    ]

    for title, key in (
        ("Decisões de deploy", "deploy_decisions_by_state"),
        ("Estados de deploy", "deployments_by_state"),
        ("Estados de verificação de efeito", "effects_by_state"),
    ):
        if key in summary:
            lines += [f"## {title}", ""]
            for state, value in sorted(summary[key].items()):
                lines.append(f"- **{state}**: {value}")
            lines.append("")

    lines += [
        "## Governança",
        "",
        "- O registro de uma decisão não prova que o deploy ocorreu.",
        "- O registro de deploy exige evidência externa explícita.",
        "- A verificação pós-deploy avalia comportamento técnico/operacional da implementação.",
        "- Nenhuma conclusão causal sobre hospitalizações, óbitos, circulação viral ou outros desfechos epidemiológicos deve ser derivada automaticamente.",
        "- Qualquer rollback ou nova mudança de regra exige decisão humana e fluxo próprio.",
        "",
    ]
    return "\n".join(lines)
