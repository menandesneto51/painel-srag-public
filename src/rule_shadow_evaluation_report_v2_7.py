# -*- coding: utf-8 -*-
from __future__ import annotations

from datetime import datetime, timezone

import pandas as pd

from src.rule_shadow_evaluation_v2_7 import summarize_shadow_evaluation


def build_shadow_metadata(
    shadow: pd.DataFrame,
    proposal_id: str,
    proposal_status: str,
    current_rule_version: str,
    candidate_rule_version: str,
) -> dict:
    summary = summarize_shadow_evaluation(shadow)
    return {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "proposal_id": proposal_id,
        "proposal_status": proposal_status,
        "current_rule_version": current_rule_version,
        "candidate_rule_version": candidate_rule_version,
        **summary,
        "workflow_agreement_is_not_epidemiological_accuracy": True,
        "candidate_rule_activated": False,
        "human_approval_required_after_shadow": True,
        "status": "shadow_evaluation_only",
    }


def render_shadow_report(
    shadow: pd.DataFrame,
    proposal_id: str,
    proposal_status: str,
    current_rule_version: str,
    candidate_rule_version: str,
) -> str:
    metadata = build_shadow_metadata(
        shadow,
        proposal_id=proposal_id,
        proposal_status=proposal_status,
        current_rule_version=current_rule_version,
        candidate_rule_version=candidate_rule_version,
    )

    lines = [
        "# Avaliação em Modo Sombra de Regra Candidata — v2.7",
        "",
        "> Avaliação em modo sombra. A regra candidata não foi ativada e nenhuma alteração é aplicada automaticamente.",
        "",
        f"- Proposta: **{proposal_id}**",
        f"- Status da proposta: **{proposal_status}**",
        f"- Versão atual: **{current_rule_version}**",
        f"- Versão candidata: **{candidate_rule_version}**",
        f"- Municípios avaliados: **{metadata['municipalities']}**",
        f"- Municípios que mudariam de fila: **{metadata['municipalities_with_queue_change']}**",
        f"- Fração com mudança de fila: **{metadata['queue_change_fraction']:.3f}**",
        "- Ativação automática: **desabilitada**",
        "- Reviewer scoring: **desabilitado**",
        "- Ranking municipal: **desabilitado**",
        "",
        "## Mudança de concordância do workflow",
        "",
    ]
    for key, value in sorted(metadata["alignment_delta_counts"].items()):
        lines.append(f"- **{key}**: {value}")

    changed = (
        shadow.drop_duplicates("codigo_ibge")
        .loc[lambda df: df["queue_changed"].astype(bool)]
    )
    lines += ["", "## Transições de fila", ""]
    if changed.empty:
        lines.append("Nenhum município mudaria de fila.")
    else:
        transitions = (
            changed["queue_transition"]
            .astype("string")
            .value_counts(dropna=False)
            .to_dict()
        )
        for key, value in sorted(transitions.items()):
            lines.append(f"- **{key}**: {int(value)} município(s)")

    lines += [
        "",
        "## Interpretação",
        "",
        "- workflow_agreement_improved significa maior concordância com decisões humanas registradas; não significa maior acurácia epidemiológica.",
        "- workflow_agreement_worsened indica menor concordância com o workflow humano; exige revisão de casos e contexto.",
        "- Decisão humana não é padrão-ouro epidemiológico.",
        "- A avaliação não autoriza alteração de regra, threshold ou configuração.",
        "",
        "## Gate posterior",
        "",
        "Depois do modo sombra, qualquer proposta deve retornar à revisão epidemiológica/estatística/documental e à aprovação humana antes de eventual merge da regra.",
        "",
    ]
    return "\n".join(lines)
