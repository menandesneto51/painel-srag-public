# -*- coding: utf-8 -*-
from __future__ import annotations

from datetime import datetime, timezone

import pandas as pd


def summarize_implementation_packages(packages: pd.DataFrame) -> dict:
    required = {
        "implementation_package_id",
        "proposal_id",
        "evaluation_record_id",
        "package_status",
        "target_branch_suggestion",
        "package_is_not_implementation",
        "manual_branch_required",
        "automatic_branch_creation_enabled",
        "automatic_code_edit_enabled",
        "automatic_commit_enabled",
        "automatic_merge_enabled",
        "automatic_deploy_enabled",
        "human_review_required",
    }
    missing = required.difference(packages.columns)
    if missing:
        raise ValueError(f"Pacotes v2.9 sem colunas: {sorted(missing)}")

    if not packages["package_is_not_implementation"].astype(bool).all():
        raise ValueError("Pacote v2.9 deve permanecer distinto de implementação.")
    if not packages["manual_branch_required"].astype(bool).all():
        raise ValueError("Branch manual deve ser obrigatória.")
    for field in (
        "automatic_branch_creation_enabled",
        "automatic_code_edit_enabled",
        "automatic_commit_enabled",
        "automatic_merge_enabled",
        "automatic_deploy_enabled",
    ):
        if packages[field].astype(bool).any():
            raise ValueError(f"{field} não pode estar habilitado.")
    if not packages["human_review_required"].astype(bool).all():
        raise ValueError("Revisão humana deve permanecer obrigatória.")

    return {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "packages": int(len(packages)),
        "packages_by_status": {
            str(k): int(v)
            for k, v in packages["package_status"]
            .astype("string")
            .value_counts(dropna=False)
            .to_dict()
            .items()
        },
        "manual_branch_required": True,
        "automatic_branch_creation": False,
        "automatic_code_edit": False,
        "automatic_commit": False,
        "automatic_merge": False,
        "automatic_deploy": False,
        "human_review_required": True,
    }


def render_implementation_package_report(packages: pd.DataFrame) -> str:
    summary = summarize_implementation_packages(packages)

    lines = [
        "# Pacotes de Implementação — v2.9",
        "",
        "> Pacote não é implementação. Nenhuma branch é criada, nenhum código é editado e nenhum merge/deploy ocorre automaticamente.",
        "",
        f"- Pacotes: **{summary['packages']}**",
        "- Branch manual: **obrigatória**",
        "- Criação automática de branch: **desabilitada**",
        "- Edição automática: **desabilitada**",
        "- Commit automático: **desabilitado**",
        "- Merge automático: **desabilitado**",
        "- Deploy automático: **desabilitado**",
        "",
        "## Pacotes",
        "",
    ]

    for row in packages.sort_values(
        ["package_status", "proposal_id", "created_at"]
    ).itertuples(index=False):
        lines += [
            f"### {row.implementation_package_id}",
            "",
            f"- Proposta: **{row.proposal_id}**",
            f"- Avaliação v2.8: **{row.evaluation_record_id}**",
            f"- Tipo: **{row.proposal_type}**",
            f"- Regra: **{row.rule_key}**",
            f"- Status: **{row.package_status}**",
            f"- Branch sugerida: **{row.target_branch_suggestion}**",
            f"- Arquivos-alvo: {row.target_paths}",
            f"- Testes requeridos: {row.required_tests}",
            f"- Critérios de aceitação: {row.acceptance_criteria}",
            f"- Rollback: {row.rollback_plan}",
            "",
        ]

    lines += [
        "## Governança",
        "",
        "O pacote apenas prepara a implementação manual. A branch deve ser criada explicitamente, o código deve ser alterado sob revisão e todos os testes devem ser repetidos antes de qualquer merge.",
        "",
    ]
    return "\n".join(lines)
