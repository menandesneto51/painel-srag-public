# -*- coding: utf-8 -*-
from __future__ import annotations

import json
from pathlib import Path

import pandas as pd


REQUIRED_LEDGER_COLUMNS = {
    "event_key",
    "stage_order",
    "event_type",
    "record_id",
    "parent_event_key",
    "event_at",
    "state",
    "proposal_id",
    "lineage_status",
    "ledger_is_not_execution",
    "ledger_does_not_trigger_actions",
    "automatic_action_enabled",
}


def load_governance_observability_config(path: Path) -> dict:
    cfg = json.loads(path.read_text(encoding="utf-8"))
    principles = cfg.get("principles") or {}

    for key in (
        "process_metrics_are_not_performance_scores",
        "no_reviewer_scoring",
        "no_municipality_ranking",
        "stale_flag_is_not_risk",
        "thresholds_are_not_institutional_sla",
        "human_review_required",
    ):
        if principles.get(key) is not True:
            raise ValueError(f"{key} deve ser true.")

    if principles.get("automatic_action") is not False:
        raise ValueError("automatic_action deve ser false.")

    threshold = cfg.get("default_stale_threshold_hours")
    if not isinstance(threshold, (int, float)) or threshold <= 0:
        raise ValueError(
            "default_stale_threshold_hours deve ser número positivo."
        )

    return cfg


def _parse_as_of(value: str | pd.Timestamp) -> pd.Timestamp:
    parsed = pd.to_datetime(value, errors="coerce", utc=True)
    if pd.isna(parsed):
        raise ValueError("as_of inválido.")
    return parsed


def _validate_ledger(ledger: pd.DataFrame) -> pd.DataFrame:
    missing = REQUIRED_LEDGER_COLUMNS.difference(ledger.columns)
    if missing:
        raise ValueError(
            f"Ledger v2.15 sem colunas obrigatórias: {sorted(missing)}"
        )

    data = ledger.copy()
    if data["event_key"].duplicated().any():
        raise ValueError("Ledger contém event_key duplicado.")
    if not data["ledger_is_not_execution"].astype(bool).all():
        raise ValueError("Ledger deve permanecer distinto de execução.")
    if not data["ledger_does_not_trigger_actions"].astype(bool).all():
        raise ValueError("Ledger não pode disparar ações.")
    if data["automatic_action_enabled"].astype(bool).any():
        raise ValueError("Ledger não pode habilitar ação automática.")
    if not data["lineage_status"].astype(str).eq(
        "linked_and_validated"
    ).all():
        raise ValueError(
            "Observabilidade só aceita ledger com linhagem validada."
        )

    data["_event_ts"] = pd.to_datetime(
        data["event_at"],
        errors="coerce",
        utc=True,
    )
    return data


def build_transition_metrics(ledger: pd.DataFrame) -> pd.DataFrame:
    data = _validate_ledger(ledger)
    lookup = data.set_index("event_key")

    rows: list[dict] = []
    for row in data.to_dict(orient="records"):
        parent_key = str(row.get("parent_event_key") or "").strip()
        if not parent_key:
            continue
        if parent_key not in lookup.index:
            raise ValueError(
                f"Evento sem pai no ledger validado: {row['event_key']}"
            )

        parent = lookup.loc[parent_key]
        child_ts = row["_event_ts"]
        parent_ts = parent["_event_ts"]

        duration_hours: float | None
        duration_status: str
        if pd.isna(child_ts) or pd.isna(parent_ts):
            duration_hours = None
            duration_status = "not_computable_missing_timestamp"
        else:
            delta = (child_ts - parent_ts).total_seconds() / 3600.0
            if delta < 0:
                raise ValueError(
                    f"Cronologia inválida: {row['event_key']} anterior ao pai."
                )
            duration_hours = float(delta)
            duration_status = "computed"

        rows.append({
            "proposal_id": str(row["proposal_id"]),
            "parent_event_key": parent_key,
            "parent_event_type": str(parent["event_type"]),
            "event_key": str(row["event_key"]),
            "event_type": str(row["event_type"]),
            "transition_hours": duration_hours,
            "duration_status": duration_status,
            "process_metric_is_not_performance_score": True,
            "reviewer_score_enabled": False,
            "municipality_rank_enabled": False,
        })

    return pd.DataFrame(rows)


def build_proposal_governance_status(
    ledger: pd.DataFrame,
    config: dict,
    as_of: str | pd.Timestamp,
) -> pd.DataFrame:
    data = _validate_ledger(ledger)
    as_of_ts = _parse_as_of(as_of)

    thresholds = {
        str(k): float(v)
        for k, v in (config.get("stage_stale_threshold_hours") or {}).items()
    }
    default_threshold = float(config["default_stale_threshold_hours"])
    terminal_stages = set(config.get("terminal_stages") or [])

    rows: list[dict] = []

    for proposal_id, group in data.groupby("proposal_id", sort=True):
        ordered = group.sort_values(
            ["stage_order", "_event_ts", "event_key"],
            kind="stable",
        )
        current = ordered.iloc[-1]
        current_stage = str(current["event_type"])
        current_state = str(current["state"])

        timestamps = ordered["_event_ts"].dropna()
        first_event_at = (
            timestamps.min().isoformat()
            if not timestamps.empty
            else ""
        )
        last_event_at = (
            timestamps.max().isoformat()
            if not timestamps.empty
            else ""
        )

        if not timestamps.empty:
            last_ts = timestamps.max()
            if as_of_ts < last_ts:
                raise ValueError(
                    f"{proposal_id}: as_of anterior ao último evento."
                )
            hours_since_last = float(
                (as_of_ts - last_ts).total_seconds() / 3600.0
            )
            total_observed_hours = float(
                (timestamps.max() - timestamps.min()).total_seconds()
                / 3600.0
            )
        else:
            hours_since_last = None
            total_observed_hours = None

        threshold = thresholds.get(
            current_stage,
            default_threshold,
        )
        terminal = current_stage in terminal_stages
        stale = bool(
            not terminal
            and hours_since_last is not None
            and hours_since_last > threshold
        )

        event_types = set(ordered["event_type"].astype(str))
        rows.append({
            "proposal_id": str(proposal_id),
            "events_count": int(len(ordered)),
            "first_event_at": first_event_at,
            "last_event_at": last_event_at,
            "current_stage": current_stage,
            "current_state": current_state,
            "stage_order": int(current["stage_order"]),
            "hours_since_last_event": hours_since_last,
            "total_observed_hours": total_observed_hours,
            "stale_threshold_hours": threshold,
            "stale_experimental": stale,
            "terminal_stage": terminal,
            "deployment_seen": "deployment" in event_types,
            "effect_verification_seen": (
                "effect_verification" in event_types
            ),
            "rollback_decision_seen": (
                "rollback_decision" in event_types
            ),
            "rollback_execution_seen": (
                "rollback_execution" in event_types
            ),
            "lineage_status": "linked_and_validated",
            "threshold_status": str(config["threshold_status"]),
            "stale_flag_is_not_risk": True,
            "process_metric_is_not_performance_score": True,
            "reviewer_score_enabled": False,
            "municipality_rank_enabled": False,
            "automatic_action_enabled": False,
            "human_review_required": True,
            "as_of": as_of_ts.isoformat(),
        })

    return pd.DataFrame(rows).sort_values(
        ["terminal_stage", "stale_experimental", "current_stage", "proposal_id"],
        ascending=[True, False, True, True],
    ).reset_index(drop=True)


def build_governance_observability_summary(
    proposal_status: pd.DataFrame,
    transition_metrics: pd.DataFrame,
) -> dict:
    required = {
        "proposal_id",
        "current_stage",
        "stale_experimental",
        "terminal_stage",
        "stale_flag_is_not_risk",
        "reviewer_score_enabled",
        "municipality_rank_enabled",
        "automatic_action_enabled",
    }
    missing = required.difference(proposal_status.columns)
    if missing:
        raise ValueError(
            f"Status v2.16 sem colunas: {sorted(missing)}"
        )

    if proposal_status["reviewer_score_enabled"].astype(bool).any():
        raise ValueError("Reviewer scoring não é permitido.")
    if proposal_status["municipality_rank_enabled"].astype(bool).any():
        raise ValueError("Ranking municipal não é permitido.")
    if proposal_status["automatic_action_enabled"].astype(bool).any():
        raise ValueError("Ação automática não é permitida.")
    if not proposal_status["stale_flag_is_not_risk"].astype(bool).all():
        raise ValueError("Stale flag deve permanecer distinto de risco.")

    computed = transition_metrics.loc[
        transition_metrics["duration_status"].eq("computed")
    ].copy() if not transition_metrics.empty else transition_metrics.copy()

    median_by_stage: dict[str, float] = {}
    if not computed.empty:
        medians = (
            computed.groupby("event_type")["transition_hours"]
            .median()
            .dropna()
        )
        median_by_stage = {
            str(k): float(v)
            for k, v in medians.to_dict().items()
        }

    return {
        "proposals": int(len(proposal_status)),
        "terminal_proposals": int(
            proposal_status["terminal_stage"].astype(bool).sum()
        ),
        "open_proposals": int(
            (~proposal_status["terminal_stage"].astype(bool)).sum()
        ),
        "stale_experimental": int(
            proposal_status["stale_experimental"].astype(bool).sum()
        ),
        "current_stage_counts": {
            str(k): int(v)
            for k, v in proposal_status["current_stage"]
            .astype("string")
            .value_counts(dropna=False)
            .to_dict()
            .items()
        },
        "median_transition_hours_by_stage": median_by_stage,
        "reviewer_scoring": False,
        "municipality_ranking": False,
        "stale_flag_is_risk": False,
        "thresholds_are_institutional_sla": False,
        "automatic_action": False,
    }
