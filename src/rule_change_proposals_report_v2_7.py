# -*- coding: utf-8 -*-
from __future__ import annotations

from datetime import datetime, timezone

import pandas as pd


def summarize_rule_change_proposals(proposals: pd.DataFrame) -> dict:
    required={
        "proposal_id","proposal_type","proposal_status","rule_key",
        "affected_records","affected_municipalities",
        "automatic_rule_change_enabled","proposal_is_not_change",
        "human_approval_required",
    }
    missing=required.difference(proposals.columns)
    if missing:
        raise ValueError(f"Propostas sem colunas: {sorted(missing)}")
    if proposals["automatic_rule_change_enabled"].astype(bool).any():
        raise ValueError("Há proposta com alteração automática habilitada.")
    if not proposals["proposal_is_not_change"].astype(bool).all():
        raise ValueError("Toda proposta deve permanecer distinta de mudança aplicada.")
    if not proposals["human_approval_required"].astype(bool).all():
        raise ValueError("Toda proposta deve exigir aprovação humana.")

    return {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "proposals": int(len(proposals)),
        "proposals_by_type": {
            str(k): int(v)
            for k,v in proposals["proposal_type"].astype("string").value_counts(dropna=False).to_dict().items()
        },
        "proposals_by_status": {
            str(k): int(v)
            for k,v in proposals["proposal_status"].astype("string").value_counts(dropna=False).to_dict().items()
        },
        "affected_records": int(pd.to_numeric(proposals["affected_records"],errors="coerce").fillna(0).sum()),
        "affected_municipalities_max": (
            int(pd.to_numeric(proposals["affected_municipalities"],errors="coerce").fillna(0).max())
            if len(proposals) else 0
        ),
        "automatic_rule_change": False,
        "automatic_threshold_change": False,
        "human_approval_required": True,
    }


def render_rule_change_proposals_report(proposals: pd.DataFrame) -> str:
    summary=summarize_rule_change_proposals(proposals)
    lines=[
        "# Propostas de Mudança de Regra — v2.7",
        "",
        "> Proposta não é mudança aplicada. Nenhuma regra ou threshold é alterado automaticamente.",
        "",
        f"- Propostas: **{summary['proposals']}**",
        f"- Registros afetados: **{summary['affected_records']}**",
        "- Alteração automática de regra: **desabilitada**",
        "- Alteração automática de threshold: **desabilitada**",
        "- Aprovação humana: **obrigatória**",
        "",
        "## Propostas",
        "",
    ]
    for row in proposals.sort_values(["proposal_type","rule_key","proposal_id"]).itertuples(index=False):
        lines += [
            f"### {row.proposal_id}",
            "",
            f"- Regra: **{row.rule_key}**",
            f"- Tipo: **{row.proposal_type}**",
            f"- Status: **{row.proposal_status}**",
            f"- Registros afetados: **{row.affected_records}**",
            f"- Municípios afetados: **{row.affected_municipalities}**",
            f"- Problema: {row.problem_statement}",
            f"- Análise requerida: {row.analysis_required}",
            "",
        ]

    lines += [
        "## Governança",
        "",
        "Qualquer proposta que altere lógica ou threshold deve passar por revisão de casos, revisão epidemiológica, backtesting, revisão estatística quando aplicável, documentação e aprovação humana.",
        "",
    ]
    return "\n".join(lines)
