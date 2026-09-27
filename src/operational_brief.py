# -*- coding: utf-8 -*-
from __future__ import annotations

from collections import Counter

import pandas as pd


def build_operational_review_queues(actions: pd.DataFrame) -> pd.DataFrame:
    required = {
        "codigo_ibge",
        "municipio",
        "action_id",
        "domain",
        "title",
        "suggested_review_owner",
        "suggested_timeframe",
        "suggestion_status",
        "human_review_required",
        "automatic_execution",
    }
    missing = required.difference(actions.columns)
    if missing:
        raise ValueError(f"Ações sem colunas obrigatórias: {sorted(missing)}")
    if actions.empty:
        return pd.DataFrame(
            columns=[
                "queue_id",
                "domain",
                "suggested_review_owner",
                "suggested_timeframe",
                "municipalities",
                "suggestions",
                "action_ids",
                "municipality_names",
                "queue_status",
            ]
        )

    if actions["automatic_execution"].fillna(False).astype(bool).any():
        raise ValueError("Fila operacional recebeu ação com execução automática habilitada.")
    if not actions["human_review_required"].fillna(False).astype(bool).all():
        raise ValueError("Toda ação da fila deve exigir revisão humana.")

    rows = []
    grouped = actions.groupby(
        ["domain", "suggested_review_owner", "suggested_timeframe"],
        dropna=False,
        sort=True,
    )
    for (domain, owner, timeframe), group in grouped:
        action_ids = sorted(group["action_id"].astype(str).unique().tolist())
        municipality_names = sorted(group["municipio"].astype(str).unique().tolist())
        queue_id = f"{domain}::{owner}::{timeframe}"
        rows.append({
            "queue_id": queue_id,
            "domain": domain,
            "suggested_review_owner": owner,
            "suggested_timeframe": timeframe,
            "municipalities": int(group["codigo_ibge"].nunique()),
            "suggestions": int(len(group)),
            "action_ids": "|".join(action_ids),
            "municipality_names": " | ".join(municipality_names),
            "queue_status": "human_review_queue",
        })
    return pd.DataFrame(rows).sort_values(
        ["suggested_timeframe", "domain", "suggested_review_owner"]
    ).reset_index(drop=True)


def build_state_operational_brief(
    actions: pd.DataFrame,
    queues: pd.DataFrame,
    reference_week: int | None = None,
) -> str:
    lines = [
        "# Briefing Estadual Operacional SRAG — v2.2",
        "",
        "> Artefato candidato para revisão humana. Não representa alerta operacional automático.",
        "",
    ]
    if reference_week is not None:
        lines.append(f"**Semana de referência:** SE {int(reference_week)}")
        lines.append("")

    if actions.empty:
        lines.extend([
            "Nenhuma sugestão de ação foi gerada pelas regras experimentais atuais.",
            "",
            "Isso não equivale a ausência de risco e não substitui revisão epidemiológica.",
        ])
        return "\n".join(lines) + "\n"

    lines.extend([
        f"**Municípios com ao menos uma sugestão:** {actions['codigo_ibge'].nunique()}",
        f"**Sugestões geradas:** {len(actions)}",
        f"**Filas de revisão:** {len(queues)}",
        "",
        "## Filas de revisão",
        "",
    ])

    for row in queues.itertuples(index=False):
        lines.extend([
            f"### {row.domain} — {row.suggested_review_owner}",
            "",
            f"- Janela sugerida: **{row.suggested_timeframe}**",
            f"- Municípios: **{row.municipalities}**",
            f"- Sugestões: **{row.suggestions}**",
            f"- Ações: {row.action_ids}",
            "",
        ])

    lines.extend([
        "## Ações por domínio",
        "",
    ])
    for domain, group in actions.groupby("domain", sort=True):
        lines.append(f"### {domain}")
        lines.append("")
        for title, action_group in group.groupby("title", sort=True):
            municipalities = sorted(action_group["municipio"].astype(str).unique().tolist())
            lines.append(f"- **{title}** — {len(municipalities)} município(s).")
        lines.append("")

    confidence_counts = Counter(actions["signal_confidence"].astype(str))
    lines.extend([
        "## Contexto de confiança dos sinais que geraram sugestões",
        "",
    ])
    for key in sorted(confidence_counts):
        lines.append(f"- {key}: {confidence_counts[key]} sugestão(ões)")
    lines.extend([
        "",
        "## Governança",
        "",
        "- Todas as ações são sugestões para revisão humana.",
        "- Nenhuma ação é executada automaticamente.",
        "- O briefing não usa score composto territorial.",
        "- Ações assistenciais dependem de fonte institucional validada quando aplicável.",
        "- Comunicação de risco deve ocorrer somente após validação epidemiológica do cenário.",
        "",
    ])
    return "\n".join(lines)
