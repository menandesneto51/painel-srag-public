# -*- coding: utf-8 -*-
from __future__ import annotations

from datetime import datetime, timezone

import pandas as pd


def summarize_rule_change_evaluations(evaluations: pd.DataFrame) -> dict:
    required = {
        "evaluation_record_id",
        "proposal_id",
        "proposal_type",
        "final_decision",
        "shadow_review_status",
        "shadow_evidence_present",
        "shadow_review_is_not_activation",
        "decision_is_not_implementation",
        "automatic_rule_change_enabled",
        "automatic_threshold_change_enabled",
        "automatic_merge_enabled",
        "automatic_deploy_enabled",
        "human_approval_required",
    }
    missing = required.difference(evaluations.columns)
    if missing:
        raise ValueError(f"Avaliações v2.8 sem colunas: {sorted(missing)}")

    if evaluations["automatic_rule_change_enabled"].astype(bool).any():
        raise ValueError("Há avaliação com alteração automática de regra.")
    if evaluations["automatic_threshold_change_enabled"].astype(bool).any():
        raise ValueError("Há avaliação com alteração automática de threshold.")
    if evaluations["automatic_merge_enabled"].astype(bool).any():
        raise ValueError("Há avaliação com merge automático habilitado.")
    if evaluations["automatic_deploy_enabled"].astype(bool).any():
        raise ValueError("Há avaliação com deploy automático habilitado.")
    if not evaluations["shadow_review_is_not_activation"].astype(bool).all():
        raise ValueError("Shadow review deve permanecer distinto de ativação.")
    if not evaluations["decision_is_not_implementation"].astype(bool).all():
        raise ValueError("Decisão v2.8 deve permanecer distinta de implementação.")
    if not evaluations["human_approval_required"].astype(bool).all():
        raise ValueError("Toda avaliação deve preservar aprovação humana.")

    return {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "evaluations": int(len(evaluations)),
        "evaluations_by_decision": {
            str(k): int(v)
            for k, v in evaluations["final_decision"]
            .astype("string")
            .value_counts(dropna=False)
            .to_dict()
            .items()
        },
        "evaluations_by_type": {
            str(k): int(v)
            for k, v in evaluations["proposal_type"]
            .astype("string")
            .value_counts(dropna=False)
            .to_dict()
            .items()
        },
        "shadow_evidence_records": int(
            evaluations["shadow_evidence_present"].astype(bool).sum()
        ),
        "automatic_rule_change": False,
        "automatic_threshold_change": False,
        "automatic_merge": False,
        "automatic_deploy": False,
        "decision_is_not_implementation": True,
        "human_approval_required": True,
    }


def render_rule_change_evaluation_report(evaluations: pd.DataFrame) -> str:
    summary = summarize_rule_change_evaluations(evaluations)
    lines = [
        "# Avaliação Formal de Propostas — v2.8",
        "",
        "> Aprovação v2.8 autoriza apenas preparação de branch de implementação. Não altera regra, threshold, main ou produção.",
        "",
        f"- Avaliações: **{summary['evaluations']}**",
        "- Alteração automática de regra: **desabilitada**",
        "- Alteração automática de threshold: **desabilitada**",
        f"- Avaliações com evidência shadow vinculada: **{summary['shadow_evidence_records']}**",
        "- Merge automático: **desabilitado**",
        "- Deploy automático: **desabilitado**",
        "",
        "## Decisões",
        "",
    ]
    for key, value in sorted(summary["evaluations_by_decision"].items()):
        lines.append(f"- **{key}**: {value}")

    lines += ["", "## Avaliações individuais", ""]
    for row in evaluations.sort_values(
        ["final_decision", "proposal_id", "evaluated_at"]
    ).itertuples(index=False):
        lines += [
            f"### {row.proposal_id}",
            "",
            f"- Tipo: **{row.proposal_type}**",
            f"- Decisão: **{row.final_decision}**",
            f"- Papel do revisor: **{row.reviewer_role}**",
            f"- Case review: **{row.case_review_status}**",
            f"- Revisão epidemiológica: **{row.epidemiology_review_status}**",
            f"- Shadow review: **{row.shadow_review_status}**",
            f"- Evidência shadow presente: **{row.shadow_evidence_present}**",
            f"- Versão candidata shadow: **{row.shadow_candidate_rule_version}**",
            f"- Backtesting: **{row.backtest_status}**",
            f"- Revisão estatística: **{row.statistical_review_status}**",
            f"- Documentação: **{row.documentation_status}**",
            f"- Impacto: {row.impact_summary}",
            f"- Riscos: {row.risk_summary}",
            f"- Justificativa: {row.decision_rationale}",
            "",
        ]

    lines += [
        "## Governança",
        "",
        "Toda proposta aprovada deve ser implementada em branch separada, novamente testada e revisada antes de qualquer merge. A aprovação v2.8 não prova implementação e não autoriza deploy automático.",
        "",
    ]
    return "\n".join(lines)
