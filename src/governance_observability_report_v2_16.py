# -*- coding: utf-8 -*-
from __future__ import annotations

from datetime import datetime, timezone

import pandas as pd

from src.governance_observability_v2_16 import (
    build_governance_observability_summary,
)


def build_governance_observability_metadata(
    proposal_status: pd.DataFrame,
    transition_metrics: pd.DataFrame,
) -> dict:
    summary = build_governance_observability_summary(
        proposal_status,
        transition_metrics,
    )
    return {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        **summary,
        "process_metrics_are_not_performance_scores": True,
        "threshold_status": "experimental_internal_not_sla",
        "human_review_required": True,
    }


def render_governance_observability_report(
    proposal_status: pd.DataFrame,
    transition_metrics: pd.DataFrame,
) -> str:
    summary = build_governance_observability_summary(
        proposal_status,
        transition_metrics,
    )

    lines = [
        "# Observabilidade do Processo de Governança — v2.16",
        "",
        "> Métricas de fluxo, não de desempenho individual. Flags de estagnação são experimentais, não SLA institucional e não representam risco epidemiológico.",
        "",
        f"- Propostas: **{summary['proposals']}**",
        f"- Em fluxo: **{summary['open_proposals']}**",
        f"- Em estágio terminal: **{summary['terminal_proposals']}**",
        f"- Flags de estagnação experimental: **{summary['stale_experimental']}**",
        "- Reviewer scoring: **desabilitado**",
        "- Ranking municipal: **desabilitado**",
        "- Ação automática: **desabilitada**",
        "",
        "## Estágio atual",
        "",
    ]
    for key, value in sorted(summary["current_stage_counts"].items()):
        lines.append(f"- **{key}**: {value}")

    lines += [
        "",
        "## Mediana observada entre transições",
        "",
    ]
    if summary["median_transition_hours_by_stage"]:
        for key, value in sorted(
            summary["median_transition_hours_by_stage"].items()
        ):
            lines.append(f"- Até **{key}**: {value:.1f} h")
    else:
        lines.append("Sem transições temporais calculáveis.")

    stale = proposal_status.loc[
        proposal_status["stale_experimental"].astype(bool)
    ].copy()
    lines += [
        "",
        "## Itens para revisão de fluxo",
        "",
    ]
    if stale.empty:
        lines.append("Nenhuma flag experimental de estagnação.")
    else:
        for row in stale.sort_values(
            ["current_stage", "hours_since_last_event"],
            ascending=[True, False],
        ).itertuples(index=False):
            hours = (
                f"{float(row.hours_since_last_event):.1f} h"
                if pd.notna(row.hours_since_last_event)
                else "não calculável"
            )
            lines.append(
                f"- **{row.proposal_id}** — {row.current_stage}; "
                f"sem novo evento por {hours}; threshold experimental "
                f"{float(row.stale_threshold_hours):.1f} h."
            )

    lines += [
        "",
        "## Governança",
        "",
        "- As métricas servem para revisar o processo e remover bloqueios.",
        "- Não devem ser usadas para avaliar produtividade ou competência de revisores.",
        "- Não devem ser usadas para ranquear municípios.",
        "- Thresholds desta versão são experimentais e não constituem SLA da SES.",
        "- Nenhuma flag gera notificação, ação ou alteração de regra automaticamente.",
        "",
    ]
    return "\n".join(lines)
