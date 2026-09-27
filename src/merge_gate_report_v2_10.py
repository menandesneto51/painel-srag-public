# -*- coding: utf-8 -*-
from __future__ import annotations

from datetime import datetime, timezone

import pandas as pd


def summarize_merge_gate(records: pd.DataFrame) -> dict:
    required = {
        "merge_gate_record_id",
        "implementation_package_id",
        "final_gate_decision",
        "merge_eligibility_is_not_merge",
        "automatic_commit_enabled",
        "automatic_merge_enabled",
        "automatic_deploy_enabled",
        "human_merge_required",
        "human_review_required",
    }
    missing = required.difference(records.columns)
    if missing:
        raise ValueError(f"Gate v2.10 sem colunas: {sorted(missing)}")

    if not records["merge_eligibility_is_not_merge"].astype(bool).all():
        raise ValueError("Elegibilidade deve permanecer distinta de merge.")
    if records["automatic_commit_enabled"].astype(bool).any():
        raise ValueError("Commit automático não é permitido.")
    if records["automatic_merge_enabled"].astype(bool).any():
        raise ValueError("Merge automático não é permitido.")
    if records["automatic_deploy_enabled"].astype(bool).any():
        raise ValueError("Deploy automático não é permitido.")
    if not records["human_merge_required"].astype(bool).all():
        raise ValueError("Merge humano deve permanecer obrigatório.")
    if not records["human_review_required"].astype(bool).all():
        raise ValueError("Revisão humana deve permanecer obrigatória.")

    return {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "records": int(len(records)),
        "decisions": {
            str(k): int(v)
            for k, v in records["final_gate_decision"]
            .astype("string")
            .value_counts(dropna=False)
            .to_dict()
            .items()
        },
        "merge_eligibility_is_not_merge": True,
        "automatic_commit": False,
        "automatic_merge": False,
        "automatic_deploy": False,
        "human_merge_required": True,
    }


def render_merge_gate_report(records: pd.DataFrame) -> str:
    summary = summarize_merge_gate(records)

    lines = [
        "# Gate de Implementação e Merge — v2.10",
        "",
        "> Elegível para merge humano não significa merge executado. Nenhum commit, merge ou deploy é realizado automaticamente.",
        "",
        f"- Registros avaliados: **{summary['records']}**",
        "- Commit automático: **desabilitado**",
        "- Merge automático: **desabilitado**",
        "- Deploy automático: **desabilitado**",
        "- Merge humano: **obrigatório**",
        "",
        "## Decisões",
        "",
    ]

    for key, value in sorted(summary["decisions"].items()):
        lines.append(f"- **{key}**: {value}")

    lines += ["", "## Registros", ""]

    for row in records.sort_values(
        ["final_gate_decision", "implementation_package_id", "evaluated_at"]
    ).itertuples(index=False):
        lines += [
            f"### {row.merge_gate_record_id}",
            "",
            f"- Pacote: **{row.implementation_package_id}**",
            f"- Proposta: **{row.proposal_id}**",
            f"- Tipo: **{row.proposal_type}**",
            f"- Branch de implementação: **{row.implementation_branch}**",
            f"- Commit-base: **{row.source_commit_sha}**",
            f"- Commit de implementação: **{row.implementation_commit_sha}**",
            f"- Diff autorizado: {row.changed_paths}",
            f"- Diff review: **{row.diff_review_status}**",
            f"- Scope review: **{row.scope_review_status}**",
            f"- CI: **{row.ci_status}**",
            f"- Regressão: **{row.regression_tests_status}**",
            f"- Backtesting: **{row.backtest_status}**",
            f"- Revalidação epidemiológica: **{row.epidemiology_revalidation_status}**",
            f"- Revalidação estatística: **{row.statistical_revalidation_status}**",
            f"- Segurança/privacidade: **{row.security_privacy_review_status}**",
            f"- Critérios de aceitação: **{row.acceptance_criteria_status}**",
            f"- Rollback: **{row.rollback_verification_status}**",
            f"- Decisão do gate: **{row.final_gate_decision}**",
            f"- Justificativa: {row.gate_rationale}",
            "",
        ]

    lines += [
        "## Governança",
        "",
        "Um registro eligible_for_human_merge autoriza somente a consideração humana do merge. A realização do merge e qualquer deploy posterior permanecem ações explícitas e separadas.",
        "",
    ]
    return "\n".join(lines)
