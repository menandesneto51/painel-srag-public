# -*- coding: utf-8 -*-
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

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


def _normalize_snapshot(frame: pd.DataFrame, snapshot_id: str) -> pd.DataFrame:
    missing = REQUIRED_QUEUE_COLUMNS.difference(frame.columns)
    if missing:
        raise ValueError(
            f"Snapshot {snapshot_id} sem colunas obrigatórias: {sorted(missing)}"
        )

    data = frame.copy()
    data["codigo_ibge"] = (
        data["codigo_ibge"]
        .astype("string")
        .str.replace(r"\.0$", "", regex=True)
        .str.zfill(7)
    )
    if len(data) != 142 or data["codigo_ibge"].nunique() != 142:
        raise ValueError(
            f"Snapshot {snapshot_id} deve conter exatamente 142 municípios."
        )
    if data["codigo_ibge"].duplicated().any():
        raise ValueError(f"Snapshot {snapshot_id} possui município duplicado.")
    if not data["human_review_required"].astype(bool).all():
        raise ValueError(
            f"Snapshot {snapshot_id} contém linha sem revisão humana obrigatória."
        )
    if data["automatic_execution_enabled"].astype(bool).any():
        raise ValueError(
            f"Snapshot {snapshot_id} contém execução automática habilitada."
        )
    if not data["queue_is_not_risk_rank"].astype(bool).all():
        raise ValueError(
            f"Snapshot {snapshot_id} permite interpretação como ranking de risco."
        )

    data["snapshot_id"] = str(snapshot_id)
    data["review_queue"] = data["review_queue"].astype("string").fillna("")
    data["review_tags"] = data["review_tags"].astype("string").fillna("")
    return data[[
        "snapshot_id",
        "codigo_ibge",
        "municipio",
        "review_queue",
        "review_tags",
    ]].sort_values("codigo_ibge").reset_index(drop=True)


def build_long_history(
    snapshots: list[tuple[str, pd.DataFrame]],
) -> pd.DataFrame:
    if not snapshots:
        raise ValueError("Nenhum snapshot informado.")

    normalized = [
        _normalize_snapshot(frame, snapshot_id)
        for snapshot_id, frame in snapshots
    ]

    reference_codes = normalized[0]["codigo_ibge"].tolist()
    for idx, frame in enumerate(normalized[1:], start=1):
        if frame["codigo_ibge"].tolist() != reference_codes:
            raise ValueError(
                f"Snapshot {snapshots[idx][0]} possui conjunto/ordem territorial divergente."
            )

    parts = []
    for order, frame in enumerate(normalized):
        copy = frame.copy()
        copy["snapshot_order"] = order
        parts.append(copy)

    return pd.concat(parts, ignore_index=True)


def _longest_run(values: list[bool]) -> int:
    best = 0
    current = 0
    for value in values:
        if value:
            current += 1
            best = max(best, current)
        else:
            current = 0
    return best


def _current_run(values: list[bool]) -> int:
    count = 0
    for value in reversed(values):
        if value:
            count += 1
        else:
            break
    return count


def _current_same_queue_run(queues: list[str]) -> int:
    if not queues:
        return 0
    current_queue = queues[-1]
    count = 0
    for queue in reversed(queues):
        if queue == current_queue:
            count += 1
        else:
            break
    return count


def _transient_single_cycle_reversions(
    queues: list[str],
    routine_queue: str,
) -> int:
    count = 0
    for i in range(1, len(queues) - 1):
        if (
            queues[i - 1] == routine_queue
            and queues[i] != routine_queue
            and queues[i + 1] == routine_queue
        ):
            count += 1
    return count


def _classify_pattern(
    queues: list[str],
    routine_queue: str,
    persistence_threshold: int,
    sustained_threshold: int,
) -> str:
    n = len(queues)
    if n < 2:
        return "insufficient_history"

    nonroutine = [q != routine_queue for q in queues]
    current_nonroutine_run = _current_run(nonroutine)
    same_queue_run = _current_same_queue_run(queues)
    changes = sum(queues[i] != queues[i - 1] for i in range(1, n))
    transient_reversions = _transient_single_cycle_reversions(
        queues, routine_queue
    )

    if all(q == routine_queue for q in queues):
        return "routine_stable"

    if (
        queues[-1] != routine_queue
        and queues[-2] == routine_queue
        and current_nonroutine_run == 1
    ):
        return "newly_entered_review"

    if (
        queues[-1] == routine_queue
        and queues[-2] != routine_queue
    ):
        if n >= 3 and queues[-3] == routine_queue:
            return "single_cycle_reversion"
        return "recently_returned_to_routine"

    if (
        queues[-1] != routine_queue
        and same_queue_run >= persistence_threshold
    ):
        return "persistent_same_queue"

    if (
        queues[-1] != routine_queue
        and current_nonroutine_run >= persistence_threshold
        and same_queue_run < current_nonroutine_run
    ):
        return "persistent_nonroutine_changed_queue"

    if transient_reversions >= 2 or changes >= max(2, n - 1):
        return "oscillating_workflow"

    return "mixed_workflow_history"


def analyze_operational_stability(
    snapshots: list[tuple[str, pd.DataFrame]],
    routine_queue: str = "routine_monitoring",
    window_vintages: int = 4,
    persistence_threshold_cycles: int = 2,
    sustained_threshold_cycles: int = 3,
) -> pd.DataFrame:
    if window_vintages < 2:
        raise ValueError("window_vintages deve ser >= 2.")
    if persistence_threshold_cycles < 2:
        raise ValueError("persistence_threshold_cycles deve ser >= 2.")
    if sustained_threshold_cycles < persistence_threshold_cycles:
        raise ValueError(
            "sustained_threshold_cycles deve ser >= persistence_threshold_cycles."
        )

    selected = snapshots[-window_vintages:]
    history = build_long_history(selected)

    rows = []
    for code, group in history.groupby("codigo_ibge", sort=True):
        ordered = group.sort_values("snapshot_order")
        queues = ordered["review_queue"].astype(str).tolist()
        tags = ordered["review_tags"].astype(str).tolist()
        nonroutine = [q != routine_queue for q in queues]

        queue_changes = sum(
            queues[i] != queues[i - 1]
            for i in range(1, len(queues))
        )
        nonroutine_cycles = sum(nonroutine)
        current_nonroutine_run = _current_run(nonroutine)
        longest_nonroutine_run = _longest_run(nonroutine)
        current_same_queue_run = _current_same_queue_run(queues)
        transient_reversions = _transient_single_cycle_reversions(
            queues, routine_queue
        )

        pattern = _classify_pattern(
            queues,
            routine_queue=routine_queue,
            persistence_threshold=persistence_threshold_cycles,
            sustained_threshold=sustained_threshold_cycles,
        )

        rows.append({
            "codigo_ibge": code,
            "municipio": str(ordered.iloc[-1]["municipio"]),
            "vintages_observed": len(queues),
            "first_snapshot_id": str(ordered.iloc[0]["snapshot_id"]),
            "current_snapshot_id": str(ordered.iloc[-1]["snapshot_id"]),
            "current_review_queue": queues[-1],
            "previous_review_queue": (
                queues[-2] if len(queues) >= 2 else pd.NA
            ),
            "distinct_review_queues": len(set(queues)),
            "nonroutine_cycles": int(nonroutine_cycles),
            "nonroutine_fraction": (
                float(nonroutine_cycles / len(queues))
                if queues else 0.0
            ),
            "current_nonroutine_run": int(current_nonroutine_run),
            "longest_nonroutine_run": int(longest_nonroutine_run),
            "current_same_queue_run": int(current_same_queue_run),
            "queue_change_count": int(queue_changes),
            "workflow_churn_rate": (
                float(queue_changes / (len(queues) - 1))
                if len(queues) > 1 else pd.NA
            ),
            "single_cycle_reversion_count": int(transient_reversions),
            "current_review_tags": tags[-1],
            "workflow_pattern": pattern,
            "persistent_2plus_cycles": bool(
                current_nonroutine_run >= persistence_threshold_cycles
            ),
            "sustained_3plus_cycles": bool(
                current_nonroutine_run >= sustained_threshold_cycles
            ),
            "workflow_stability_is_not_risk": True,
            "persistence_is_not_severity": True,
            "transience_is_not_reassurance": True,
            "automatic_action_enabled": False,
            "human_review_required": True,
            "operational_stability_status": "experimental_workflow_context",
        })

    out = pd.DataFrame(rows)
    if len(out) != 142 or out["codigo_ibge"].nunique() != 142:
        raise ValueError("Estabilidade operacional deve cobrir 142 municípios.")
    return out.sort_values("codigo_ibge").reset_index(drop=True)


def summarize_operational_stability(
    stability: pd.DataFrame,
) -> pd.DataFrame:
    required = {"workflow_pattern", "codigo_ibge"}
    missing = required.difference(stability.columns)
    if missing:
        raise ValueError(f"Estabilidade sem colunas: {sorted(missing)}")

    return (
        stability.groupby("workflow_pattern", as_index=False)
        .agg(municipalities=("codigo_ibge", "nunique"))
        .sort_values(
            ["municipalities", "workflow_pattern"],
            ascending=[False, True],
        )
        .reset_index(drop=True)
    )


def render_operational_stability_report(
    stability: pd.DataFrame,
) -> str:
    summary = summarize_operational_stability(stability)
    lines = [
        "# Estabilidade Operacional das Filas — v2.4",
        "",
        "> Estabilidade de workflow não representa risco, gravidade ou prioridade clínica.",
        "",
        f"- Municípios: **{stability['codigo_ibge'].nunique()}**",
        "- Ranking: **não utilizado**",
        "- Ação automática: **desabilitada**",
        "",
        "## Padrões de workflow",
        "",
    ]

    for row in summary.itertuples(index=False):
        lines.append(
            f"- **{row.workflow_pattern}**: {row.municipalities}"
        )

    lines += [
        "",
        "## Contexto de persistência",
        "",
    ]
    focus = stability.loc[
        stability["workflow_pattern"].isin([
            "persistent_same_queue",
            "persistent_nonroutine_changed_queue",
            "oscillating_workflow",
            "single_cycle_reversion",
        ])
    ].sort_values(["workflow_pattern", "municipio"])

    if focus.empty:
        lines.append("Nenhum município nos padrões selecionados.")
    else:
        for row in focus.itertuples(index=False):
            lines.append(
                f"- {row.municipio}: {row.workflow_pattern}; "
                f"fila atual={row.current_review_queue}; "
                f"run não rotina={row.current_nonroutine_run}; "
                f"mudanças={row.queue_change_count}."
            )

    lines += [
        "",
        "## Governança",
        "",
        "Persistência e churn servem apenas para contextualizar continuidade do workflow. Não autorizam escalonamento automático.",
        "",
    ]
    return "\n".join(lines)
