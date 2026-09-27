# -*- coding: utf-8 -*-
from __future__ import annotations

from dataclasses import dataclass

import pandas as pd


REQUIRED_QUEUE_COLUMNS = {
    "codigo_ibge",
    "municipio",
    "review_queue",
    "review_tags",
    "human_review_required",
    "automatic_execution_enabled",
    "queue_is_not_risk_rank",
}


def _normalize_queue(frame: pd.DataFrame) -> pd.DataFrame:
    missing = REQUIRED_QUEUE_COLUMNS.difference(frame.columns)
    if missing:
        raise ValueError(f"Fila operacional sem colunas: {sorted(missing)}")

    data = frame.copy()
    data["codigo_ibge"] = (
        data["codigo_ibge"]
        .astype("string")
        .str.replace(r"\.0$", "", regex=True)
        .str.zfill(7)
    )
    if data["codigo_ibge"].duplicated().any():
        raise ValueError("Fila operacional possui município duplicado.")
    if len(data) != 142 or data["codigo_ibge"].nunique() != 142:
        raise ValueError("Fila operacional deve conter exatamente 142 municípios.")

    if not data["human_review_required"].astype(bool).all():
        raise ValueError("Todas as linhas devem exigir revisão humana.")
    if data["automatic_execution_enabled"].astype(bool).any():
        raise ValueError("Execução automática não pode estar habilitada.")
    if not data["queue_is_not_risk_rank"].astype(bool).all():
        raise ValueError("Fila operacional não pode ser interpretada como ranking de risco.")

    data["review_queue"] = data["review_queue"].astype("string").fillna("")
    data["review_tags"] = data["review_tags"].astype("string").fillna("")
    return data.sort_values("codigo_ibge").reset_index(drop=True)


def _tag_set(value: object) -> set[str]:
    if value is None or pd.isna(value):
        return set()
    return {x.strip() for x in str(value).split("|") if x.strip()}


def compare_operational_vintages(
    current: pd.DataFrame,
    previous: pd.DataFrame | None,
    routine_queue: str = "routine_monitoring",
    current_snapshot_id: str | None = None,
    previous_snapshot_id: str | None = None,
) -> pd.DataFrame:
    cur = _normalize_queue(current)

    if previous is None:
        out = cur[[
            "codigo_ibge",
            "municipio",
            "review_queue",
            "review_tags",
        ]].copy()
        out["previous_review_queue"] = pd.NA
        out["previous_review_tags"] = pd.NA
        out["change_state"] = out["review_queue"].map(
            lambda q: (
                "baseline_snapshot_routine"
                if str(q) == routine_queue
                else "baseline_snapshot_nonroutine"
            )
        )
        out["new_review_tags"] = out["review_tags"]
        out["resolved_review_tags"] = ""
    else:
        prev = _normalize_queue(previous)
        merged = cur.merge(
            prev[[
                "codigo_ibge",
                "review_queue",
                "review_tags",
            ]].rename(columns={
                "review_queue": "previous_review_queue",
                "review_tags": "previous_review_tags",
            }),
            on="codigo_ibge",
            how="left",
            validate="one_to_one",
        )

        states = []
        new_tags = []
        resolved_tags = []
        for row in merged.itertuples(index=False):
            current_queue = str(row.review_queue)
            previous_queue = str(row.previous_review_queue)
            cur_tags = _tag_set(row.review_tags)
            prev_tags = _tag_set(row.previous_review_tags)

            if previous_queue == routine_queue and current_queue == routine_queue:
                state = "routine_stable"
            elif previous_queue == routine_queue and current_queue != routine_queue:
                state = "entered_review"
            elif previous_queue != routine_queue and current_queue == routine_queue:
                state = "returned_to_routine"
            elif previous_queue == current_queue:
                state = "persistent_same_queue"
            else:
                state = "changed_review_queue"

            states.append(state)
            new_tags.append("|".join(sorted(cur_tags.difference(prev_tags))))
            resolved_tags.append("|".join(sorted(prev_tags.difference(cur_tags))))

        merged["change_state"] = states
        merged["new_review_tags"] = new_tags
        merged["resolved_review_tags"] = resolved_tags
        out = merged

    out["current_snapshot_id"] = current_snapshot_id or ""
    out["previous_snapshot_id"] = previous_snapshot_id or ""
    out["change_state_is_not_risk"] = True
    out["persistence_is_not_severity"] = True
    out["automatic_action_enabled"] = False
    out["human_review_required"] = True
    out["persistence_model_status"] = "experimental_review_history"

    columns = [
        "codigo_ibge",
        "municipio",
        "review_queue",
        "previous_review_queue",
        "change_state",
        "review_tags",
        "previous_review_tags",
        "new_review_tags",
        "resolved_review_tags",
        "current_snapshot_id",
        "previous_snapshot_id",
        "change_state_is_not_risk",
        "persistence_is_not_severity",
        "automatic_action_enabled",
        "human_review_required",
        "persistence_model_status",
    ]
    return out[columns].sort_values("codigo_ibge").reset_index(drop=True)


def summarize_operational_changes(changes: pd.DataFrame) -> pd.DataFrame:
    if "change_state" not in changes.columns:
        raise ValueError("Tabela de mudanças sem change_state.")
    return (
        changes.groupby("change_state", as_index=False)
        .agg(municipalities=("codigo_ibge", "nunique"))
        .sort_values(["municipalities", "change_state"], ascending=[False, True])
        .reset_index(drop=True)
    )


def render_operational_change_report(changes: pd.DataFrame) -> str:
    summary = summarize_operational_changes(changes)
    lines = [
        "# Mudanças entre Vintages da Revisão Operacional — v2.3",
        "",
        "> Persistência ou mudança de fila não representa aumento/redução de risco. Este relatório organiza a revisão humana entre snapshots.",
        "",
        f"- Municípios: **{changes['codigo_ibge'].nunique()}**",
        "- Ranking: **não utilizado**",
        "- Ação automática: **desabilitada**",
        "",
        "## Estados de mudança",
        "",
    ]
    for row in summary.itertuples(index=False):
        lines.append(f"- **{row.change_state}**: {row.municipalities}")

    lines += ["", "## Municípios que entraram/mudaram de revisão", ""]
    focus = changes.loc[
        changes["change_state"].isin(
            ["entered_review", "changed_review_queue", "persistent_same_queue"]
        )
    ].sort_values(["change_state", "municipio"])
    if focus.empty:
        lines.append("Nenhum município.")
    else:
        for row in focus.itertuples(index=False):
            lines.append(
                f"- {row.municipio}: {row.change_state} — "
                f"{row.previous_review_queue} → {row.review_queue}"
            )

    lines += [
        "",
        "## Governança",
        "",
        "A persistência serve para contextualizar o trabalho de revisão. Não cria prioridade clínica, score ou alerta automático.",
        "",
    ]
    return "\n".join(lines)
