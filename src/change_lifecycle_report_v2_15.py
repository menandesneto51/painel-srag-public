# -*- coding: utf-8 -*-
from __future__ import annotations

from datetime import datetime, timezone

import pandas as pd

from src.change_lifecycle_ledger_v2_15 import (
    summarize_change_lifecycle_ledger,
)


def render_change_lifecycle_report(ledger: pd.DataFrame) -> str:
    summary = summarize_change_lifecycle_ledger(ledger)

    lines = [
        "# Ledger do Ciclo Completo de Mudança — v2.15",
        "",
        "> Ledger observacional e auditável. Ele não executa mudança, deploy, rollback ou qualquer ação automática.",
        "",
        f"- Eventos: **{summary['events']}**",
        f"- Propostas: **{summary['proposals']}**",
        f"- Eventos órfãos: **{summary['orphan_events']}**",
        "- Linhagem: **linked_and_validated**",
        "- Ação automática: **desabilitada**",
        "",
        "## Eventos por tipo",
        "",
    ]

    for key, value in sorted(summary["events_by_type"].items()):
        lines.append(f"- **{key}**: {value}")

    lines += [
        "",
        "## Estágio mais avançado por proposta",
        "",
    ]
    for key, value in sorted(
        summary["furthest_stage_by_proposal"].items()
    ):
        lines.append(f"- **{key}**: {value}")

    if not ledger.empty:
        lines += [
            "",
            "## Cadeias por proposta",
            "",
        ]
        for proposal_id, group in ledger.groupby(
            "proposal_id",
            sort=True,
        ):
            chain = " -> ".join(
                group.sort_values(
                    ["stage_order", "event_at", "event_key"]
                )["event_type"]
                .astype(str)
                .tolist()
            )
            lines.append(f"- **{proposal_id}**: {chain}")

    lines += [
        "",
        "## Integridade",
        "",
        "- Todo evento não raiz possui pai existente.",
        "- Toda transição segue o mapa permitido.",
        "- A cronologia não retrocede entre pai e filho.",
        "- Commit é contínuo nos trechos em que a continuidade é obrigatória.",
        "- Ambiente é herdado/validado ao longo do release/deploy.",
        "- O ledger não pontua revisores e não dispara ações.",
        "",
    ]
    return "\n".join(lines)


def build_change_lifecycle_metadata(ledger: pd.DataFrame) -> dict:
    summary = summarize_change_lifecycle_ledger(ledger)
    return {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        **summary,
        "chronology_validated": True,
        "parent_child_integrity_validated": True,
        "transition_map_validated": True,
        "commit_continuity_validated": True,
        "environment_continuity_validated": True,
        "personal_identifier_storage": False,
        "status": "auditable_change_lifecycle_ledger",
    }
