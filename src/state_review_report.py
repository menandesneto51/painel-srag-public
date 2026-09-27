# -*- coding: utf-8 -*-
from __future__ import annotations

from datetime import datetime, timezone

import pandas as pd


def build_state_review_summary(queue: pd.DataFrame) -> dict:
    required = {
        "codigo_ibge",
        "municipio",
        "review_queue",
        "review_tags",
        "human_review_required",
        "queue_is_not_risk_rank",
    }
    missing = required.difference(queue.columns)
    if missing:
        raise ValueError(f"Fila operacional sem colunas: {sorted(missing)}")

    if not queue["human_review_required"].astype(bool).all():
        raise ValueError("Há linha sem revisão humana obrigatória.")
    if not queue["queue_is_not_risk_rank"].astype(bool).all():
        raise ValueError("A fila não pode ser interpretada como ranking de risco.")

    counts = (
        queue["review_queue"]
        .astype("string")
        .value_counts(dropna=False)
        .to_dict()
    )
    municipalities = {
        str(name): sorted(group["municipio"].astype(str).tolist())
        for name, group in queue.groupby("review_queue", dropna=False)
    }

    return {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "municipality_count": int(queue["codigo_ibge"].nunique()),
        "rows": int(len(queue)),
        "queue_is_not_risk_rank": True,
        "automatic_execution_enabled": False,
        "counts_by_review_queue": {str(k): int(v) for k, v in counts.items()},
        "municipalities_by_review_queue": municipalities,
    }


def render_state_review_markdown(queue: pd.DataFrame) -> str:
    summary = build_state_review_summary(queue)

    lines = [
        "# Relatório Estadual de Revisão SRAG — v2.2",
        "",
        "> Artefato experimental de organização do trabalho. As filas abaixo não são classes de risco, não constituem alerta e não executam ações automaticamente.",
        "",
        f"- Municípios: **{summary['municipality_count']}**",
        "- Revisão humana: **obrigatória**",
        "- Score composto: **não utilizado**",
        "- Execução automática: **desabilitada**",
        "",
        "## Distribuição por fila de revisão",
        "",
    ]

    for queue_name, count in sorted(
        summary["counts_by_review_queue"].items(),
        key=lambda item: (-item[1], item[0]),
    ):
        lines.append(f"- **{queue_name}**: {count}")

    lines += ["", "## Municípios por fila", ""]
    for queue_name, municipalities in sorted(
        summary["municipalities_by_review_queue"].items()
    ):
        lines.append(f"### {queue_name}")
        lines.append("")
        if municipalities:
            lines.append(", ".join(municipalities))
        else:
            lines.append("Nenhum município.")
        lines.append("")

    lines += [
        "## Regra de governança",
        "",
        "A fila serve para organizar revisão técnica. Qualquer escalonamento ou ação institucional depende de validação do contexto, evidências disponíveis e decisão humana responsável.",
        "",
    ]
    return "\n".join(lines)
