# -*- coding: utf-8 -*-
from __future__ import annotations

from datetime import datetime, timezone

import pandas as pd


def build_rule_change_proposal_metadata(proposals: pd.DataFrame) -> dict:
    required = {
        "proposal_id",
        "proposal_type",
        "proposal_status",
        "affected_records",
        "affected_municipalities",
        "automatic_rule_change_enabled",
        "automatic_threshold_change_enabled",
        "proposal_is_not_change",
        "human_approval_required",
    }
    missing = required.difference(proposals.columns)
    if missing:
        raise ValueError(
            f"Registro de propostas sem colunas: {sorted(missing)}"
        )

    if proposals["automatic_rule_change_enabled"].astype(bool).any():
        raise ValueError("Registro contém alteração automática de regra.")
    if proposals["automatic_threshold_change_enabled"].astype(bool).any():
        raise ValueError("Registro contém alteração automática de threshold.")
    if not proposals["proposal_is_not_change"].astype(bool).all():
        raise ValueError("Toda proposta deve permanecer distinta da mudança aplicada.")
    if not proposals["human_approval_required"].astype(bool).all():
        raise ValueError("Toda proposta deve exigir aprovação humana.")

    return {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "proposal_count": int(len(proposals)),
        "affected_record_mentions": int(
            pd.to_numeric(
                proposals["affected_records"], errors="coerce"
            ).fillna(0).sum()
        ),
        "affected_municipality_mentions": int(
            pd.to_numeric(
                proposals["affected_municipalities"], errors="coerce"
            ).fillna(0).sum()
        ),
        "proposal_status_counts": {
            str(k): int(v)
            for k, v in proposals["proposal_status"]
            .astype("string")
            .value_counts(dropna=False)
            .to_dict()
            .items()
        },
        "proposal_type_counts": {
            str(k): int(v)
            for k, v in proposals["proposal_type"]
            .astype("string")
            .value_counts(dropna=False)
            .to_dict()
            .items()
        },
        "automatic_rule_change": False,
        "automatic_threshold_change": False,
        "proposal_is_not_change": True,
        "human_approval_required": True,
        "status": "experimental_governance_registry",
    }


def render_rule_change_proposal_report(proposals: pd.DataFrame) -> str:
    metadata = build_rule_change_proposal_metadata(proposals)

    lines = [
        "# Registro de Propostas de Mudança de Regra — v2.7",
        "",
        "> Proposta não é mudança aplicada. Este relatório organiza revisão humana e não seleciona automaticamente uma nova regra.",
        "",
        f"- Propostas: **{metadata['proposal_count']}**",
        f"- Menções de registros afetados: **{metadata['affected_record_mentions']}**",
        f"- Menções de municípios afetados: **{metadata['affected_municipality_mentions']}**",
        "- Alteração automática de regra: **desabilitada**",
        "- Alteração automática de threshold: **desabilitada**",
        "- Aprovação humana: **obrigatória**",
        "",
        "## Propostas",
        "",
    ]

    if proposals.empty:
        lines.append("Nenhuma proposta gerada.")
    else:
        for row in proposals.sort_values(
            ["proposal_type", "rule_key", "workflow_alignment"]
        ).itertuples(index=False):
            lines.extend([
                f"### {row.proposal_id}",
                "",
                f"- Regra: {row.rule_key}",
                f"- Tipo: {row.proposal_type}",
                f"- Estado: {row.proposal_status}",
                f"- Classe de origem: {row.workflow_alignment}",
                f"- Registros afetados: {row.affected_records}",
                f"- Municípios afetados: {row.affected_municipalities}",
                f"- Problema: {row.problem_statement}",
                f"- Análises requeridas: {row.analysis_required}",
                "",
            ])

    lines += [
        "## Governança",
        "",
        "Nenhuma proposta pode alterar a matriz vigente sem revisão dos casos, avaliação epidemiológica, backtesting quando aplicável, documentação e aprovação humana.",
        "",
    ]
    return "\n".join(lines)
