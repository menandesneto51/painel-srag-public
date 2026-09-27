# -*- coding: utf-8 -*-
from __future__ import annotations

from datetime import datetime, timezone

import pandas as pd


def build_decision_audit_summary(
    decisions: pd.DataFrame,
    follow_up_status: pd.DataFrame | None = None,
) -> dict:
    required = {
        "decision_record_id",
        "codigo_ibge",
        "decision_scope",
        "reviewer_role",
        "decision_status",
        "follow_up_required",
        "decision_recorded_by_human",
        "automatic_execution_enabled",
        "decision_is_not_proof_of_execution",
    }
    missing = required.difference(decisions.columns)
    if missing:
        raise ValueError(f"Decisões sem colunas: {sorted(missing)}")

    if not decisions["decision_recorded_by_human"].astype(bool).all():
        raise ValueError("Há decisão que não está marcada como humana.")
    if decisions["automatic_execution_enabled"].astype(bool).any():
        raise ValueError("Há decisão com execução automática habilitada.")
    if not decisions["decision_is_not_proof_of_execution"].astype(bool).all():
        raise ValueError("Decisão deve permanecer distinta de prova de execução.")

    summary = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "decision_records": int(len(decisions)),
        "municipalities_with_decisions": int(
            decisions["codigo_ibge"].nunique()
        ),
        "decisions_by_status": {
            str(k): int(v)
            for k, v in decisions["decision_status"]
            .astype("string")
            .value_counts(dropna=False)
            .to_dict()
            .items()
        },
        "decisions_by_scope": {
            str(k): int(v)
            for k, v in decisions["decision_scope"]
            .astype("string")
            .value_counts(dropna=False)
            .to_dict()
            .items()
        },
        "decisions_by_reviewer_role": {
            str(k): int(v)
            for k, v in decisions["reviewer_role"]
            .astype("string")
            .value_counts(dropna=False)
            .to_dict()
            .items()
        },
        "follow_up_required": int(
            decisions["follow_up_required"].astype(bool).sum()
        ),
        "automatic_execution_enabled": False,
        "decision_is_not_proof_of_execution": True,
        "personal_identifier_storage": False,
    }

    if follow_up_status is not None and not follow_up_status.empty:
        required_follow = {
            "decision_record_id",
            "follow_up_state",
            "automatic_execution_enabled",
            "follow_up_state_is_not_risk",
        }
        missing_follow = required_follow.difference(follow_up_status.columns)
        if missing_follow:
            raise ValueError(
                f"Status de follow-up sem colunas: {sorted(missing_follow)}"
            )
        if follow_up_status["automatic_execution_enabled"].astype(bool).any():
            raise ValueError("Follow-up com execução automática habilitada.")
        if not follow_up_status["follow_up_state_is_not_risk"].astype(bool).all():
            raise ValueError("Estado de follow-up não pode ser interpretado como risco.")

        summary["follow_up_by_state"] = {
            str(k): int(v)
            for k, v in follow_up_status["follow_up_state"]
            .astype("string")
            .value_counts(dropna=False)
            .to_dict()
            .items()
        }

    return summary


def render_decision_audit_markdown(
    decisions: pd.DataFrame,
    follow_up_status: pd.DataFrame | None = None,
) -> str:
    summary = build_decision_audit_summary(decisions, follow_up_status)

    lines = [
        "# Auditoria Estadual de Decisões Humanas — v2.5",
        "",
        "> Registro de decisão humana e follow-up. Não é prova de execução externa, não é ranking e não aciona ações automaticamente.",
        "",
        f"- Decisões registradas: **{summary['decision_records']}**",
        f"- Municípios com decisão: **{summary['municipalities_with_decisions']}**",
        f"- Follow-ups requeridos: **{summary['follow_up_required']}**",
        "- Identificadores pessoais do revisor: **não armazenados**",
        "- Execução automática: **desabilitada**",
        "",
        "## Decisões por status",
        "",
    ]
    for key, value in sorted(summary["decisions_by_status"].items()):
        lines.append(f"- **{key}**: {value}")

    lines += ["", "## Decisões por escopo", ""]
    for key, value in sorted(summary["decisions_by_scope"].items()):
        lines.append(f"- **{key}**: {value}")

    lines += ["", "## Decisões por papel do revisor", ""]
    for key, value in sorted(summary["decisions_by_reviewer_role"].items()):
        lines.append(f"- **{key}**: {value}")

    if "follow_up_by_state" in summary:
        lines += ["", "## Follow-up por estado", ""]
        for key, value in sorted(summary["follow_up_by_state"].items()):
            lines.append(f"- **{key}**: {value}")

    lines += [
        "",
        "## Governança",
        "",
        "- Uma decisão registrada não prova que uma ação externa foi executada.",
        "- Um follow-up concluído prova apenas que o evento de follow-up foi registrado como concluído pelo revisor humano.",
        "- Nenhum status de follow-up é classe de risco.",
        "- Nenhum artefato v2.5 executa ações automaticamente.",
        "",
    ]
    return "\n".join(lines)
