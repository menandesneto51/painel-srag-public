# -*- coding: utf-8 -*-
from __future__ import annotations

import json
import re
from pathlib import Path

import pandas as pd


def load_ledger_config(path: Path) -> dict:
    cfg = json.loads(path.read_text(encoding="utf-8"))
    principles = cfg.get("principles") or {}

    for key in (
        "ledger_is_not_execution",
        "ledger_does_not_trigger_actions",
        "human_review_required",
    ):
        if principles.get(key) is not True:
            raise ValueError(f"{key} deve ser true.")

    for key in ("automatic_action", "personal_identifier_storage"):
        if principles.get(key) is not False:
            raise ValueError(f"{key} deve ser false.")

    return cfg


def _blank(value: object) -> bool:
    return value is None or pd.isna(value) or str(value).strip() == ""


def _text(row: dict, key: str) -> str:
    value = row.get(key)
    return "" if _blank(value) else str(value).strip()


def _sha_or_blank(value: object, field: str) -> str:
    if _blank(value):
        return ""
    text = str(value).strip().lower()
    if not re.fullmatch(r"[0-9a-f]{40}", text):
        raise ValueError(
            f"{field} deve ser SHA Git completo de 40 caracteres hexadecimais."
        )
    return text


def _require_columns(
    frame: pd.DataFrame | None,
    columns: set[str],
    label: str,
) -> None:
    if frame is None or frame.empty:
        return
    missing = columns.difference(frame.columns)
    if missing:
        raise ValueError(f"{label} sem colunas: {sorted(missing)}")


def _event(
    *,
    event_type: str,
    record_id: str,
    parent_event_type: str = "",
    parent_record_id: str = "",
    event_at: str = "",
    state: str = "",
    proposal_id: str = "",
    implementation_package_id: str = "",
    commit_sha: str = "",
    environment: str = "",
) -> dict:
    if not record_id:
        raise ValueError(f"{event_type}: record_id vazio.")
    return {
        "event_type": event_type,
        "record_id": record_id,
        "parent_event_type": parent_event_type,
        "parent_record_id": parent_record_id,
        "event_at": event_at,
        "state": state,
        "proposal_id": proposal_id,
        "implementation_package_id": implementation_package_id,
        "commit_sha": commit_sha,
        "environment": environment.lower() if environment else "",
    }


def _append_static(
    events: list[dict],
    frame: pd.DataFrame | None,
    *,
    label: str,
    required: set[str],
    event_type: str,
    id_col: str,
    parent_event_type: str = "",
    parent_col: str = "",
    state_col: str = "",
    event_at_col: str = "",
    proposal_col: str = "",
    package_col: str = "",
    commit_col: str = "",
    environment_col: str = "",
) -> None:
    _require_columns(frame, required, label)
    if frame is None or frame.empty:
        return

    for row in frame.to_dict(orient="records"):
        events.append(
            _event(
                event_type=event_type,
                record_id=_text(row, id_col),
                parent_event_type=parent_event_type,
                parent_record_id=_text(row, parent_col) if parent_col else "",
                event_at=_text(row, event_at_col) if event_at_col else "",
                state=_text(row, state_col) if state_col else "",
                proposal_id=_text(row, proposal_col) if proposal_col else "",
                implementation_package_id=(
                    _text(row, package_col) if package_col else ""
                ),
                commit_sha=(
                    _sha_or_blank(row.get(commit_col), commit_col)
                    if commit_col else ""
                ),
                environment=(
                    _text(row, environment_col) if environment_col else ""
                ),
            )
        )


def build_change_lifecycle_ledger(
    *,
    proposals: pd.DataFrame,
    evaluations: pd.DataFrame | None = None,
    packages: pd.DataFrame | None = None,
    merge_gates: pd.DataFrame | None = None,
    merge_decisions: pd.DataFrame | None = None,
    post_merge: pd.DataFrame | None = None,
    release_gates: pd.DataFrame | None = None,
    deploy_decisions: pd.DataFrame | None = None,
    deployments: pd.DataFrame | None = None,
    effects: pd.DataFrame | None = None,
    rollback_decisions: pd.DataFrame | None = None,
    rollback_executions: pd.DataFrame | None = None,
    config: dict,
) -> pd.DataFrame:
    _require_columns(
        proposals,
        {"proposal_id", "proposal_status"},
        "Propostas v2.7",
    )
    events: list[dict] = []

    _append_static(
        events,
        proposals,
        label="Propostas v2.7",
        required={"proposal_id", "proposal_status"},
        event_type="proposal",
        id_col="proposal_id",
        state_col="proposal_status",
        proposal_col="proposal_id",
    )
    _append_static(
        events,
        evaluations,
        label="Avaliações v2.8",
        required={
            "evaluation_record_id",
            "proposal_id",
            "evaluated_at",
            "final_decision",
        },
        event_type="evaluation",
        id_col="evaluation_record_id",
        parent_event_type="proposal",
        parent_col="proposal_id",
        state_col="final_decision",
        event_at_col="evaluated_at",
        proposal_col="proposal_id",
    )
    _append_static(
        events,
        packages,
        label="Pacotes v2.9",
        required={
            "implementation_package_id",
            "proposal_id",
            "evaluation_record_id",
            "created_at",
            "package_status",
        },
        event_type="implementation_package",
        id_col="implementation_package_id",
        parent_event_type="evaluation",
        parent_col="evaluation_record_id",
        state_col="package_status",
        event_at_col="created_at",
        proposal_col="proposal_id",
        package_col="implementation_package_id",
        commit_col=(
            "source_commit_sha"
            if packages is not None and "source_commit_sha" in packages.columns
            else ""
        ),
    )
    _append_static(
        events,
        merge_gates,
        label="Merge gate v2.10",
        required={
            "merge_gate_record_id",
            "implementation_package_id",
            "proposal_id",
            "evaluated_at",
            "final_gate_decision",
            "implementation_commit_sha",
        },
        event_type="merge_gate",
        id_col="merge_gate_record_id",
        parent_event_type="implementation_package",
        parent_col="implementation_package_id",
        state_col="final_gate_decision",
        event_at_col="evaluated_at",
        proposal_col="proposal_id",
        package_col="implementation_package_id",
        commit_col="implementation_commit_sha",
    )
    _append_static(
        events,
        merge_decisions,
        label="Decisões de merge v2.11",
        required={
            "merge_decision_record_id",
            "merge_gate_record_id",
            "implementation_package_id",
            "proposal_id",
            "decided_at",
            "merge_decision",
            "implementation_commit_sha",
        },
        event_type="merge_decision",
        id_col="merge_decision_record_id",
        parent_event_type="merge_gate",
        parent_col="merge_gate_record_id",
        state_col="merge_decision",
        event_at_col="decided_at",
        proposal_col="proposal_id",
        package_col="implementation_package_id",
        commit_col="implementation_commit_sha",
    )
    _append_static(
        events,
        post_merge,
        label="Pós-merge v2.11",
        required={
            "post_merge_record_id",
            "merge_decision_record_id",
            "implementation_package_id",
            "recorded_at",
            "post_merge_state",
            "merged_commit_sha",
        },
        event_type="post_merge",
        id_col="post_merge_record_id",
        parent_event_type="merge_decision",
        parent_col="merge_decision_record_id",
        state_col="post_merge_state",
        event_at_col="recorded_at",
        package_col="implementation_package_id",
        commit_col="merged_commit_sha",
    )
    _append_static(
        events,
        release_gates,
        label="Release gate v2.12",
        required={
            "release_gate_record_id",
            "post_merge_record_id",
            "implementation_package_id",
            "evaluated_at",
            "final_release_decision",
            "release_commit_sha",
            "target_environment",
        },
        event_type="release_gate",
        id_col="release_gate_record_id",
        parent_event_type="post_merge",
        parent_col="post_merge_record_id",
        state_col="final_release_decision",
        event_at_col="evaluated_at",
        package_col="implementation_package_id",
        commit_col="release_commit_sha",
        environment_col="target_environment",
    )
    _append_static(
        events,
        deploy_decisions,
        label="Decisões de deploy v2.12",
        required={
            "deploy_decision_record_id",
            "release_gate_record_id",
            "implementation_package_id",
            "decided_at",
            "deploy_decision",
            "release_commit_sha",
            "target_environment",
        },
        event_type="deploy_decision",
        id_col="deploy_decision_record_id",
        parent_event_type="release_gate",
        parent_col="release_gate_record_id",
        state_col="deploy_decision",
        event_at_col="decided_at",
        package_col="implementation_package_id",
        commit_col="release_commit_sha",
        environment_col="target_environment",
    )
    _append_static(
        events,
        deployments,
        label="Deploys v2.12",
        required={
            "deployment_record_id",
            "deploy_decision_record_id",
            "implementation_package_id",
            "deployed_at",
            "deployment_state",
            "deployed_commit_sha",
            "environment",
        },
        event_type="deployment",
        id_col="deployment_record_id",
        parent_event_type="deploy_decision",
        parent_col="deploy_decision_record_id",
        state_col="deployment_state",
        event_at_col="deployed_at",
        package_col="implementation_package_id",
        commit_col="deployed_commit_sha",
        environment_col="environment",
    )
    _append_static(
        events,
        effects,
        label="Efeitos v2.12",
        required={
            "effect_verification_record_id",
            "deployment_record_id",
            "implementation_package_id",
            "measured_at",
            "effect_state",
            "deployed_commit_sha",
        },
        event_type="effect_verification",
        id_col="effect_verification_record_id",
        parent_event_type="deployment",
        parent_col="deployment_record_id",
        state_col="effect_state",
        event_at_col="measured_at",
        package_col="implementation_package_id",
        commit_col="deployed_commit_sha",
    )

    _require_columns(
        rollback_decisions,
        {
            "rollback_decision_record_id",
            "source_record_type",
            "source_record_id",
            "implementation_package_id",
            "decided_at",
            "rollback_decision",
            "rollback_target_commit_sha",
        },
        "Decisões de rollback v2.13",
    )
    if rollback_decisions is not None and not rollback_decisions.empty:
        parent_type_map = {
            "deployment": "deployment",
            "effect": "effect_verification",
        }
        for row in rollback_decisions.to_dict(orient="records"):
            source_type = _text(row, "source_record_type")
            if source_type not in parent_type_map:
                raise ValueError(
                    f"source_record_type inválido no rollback: {source_type}"
                )
            events.append(
                _event(
                    event_type="rollback_decision",
                    record_id=_text(row, "rollback_decision_record_id"),
                    parent_event_type=parent_type_map[source_type],
                    parent_record_id=_text(row, "source_record_id"),
                    event_at=_text(row, "decided_at"),
                    state=_text(row, "rollback_decision"),
                    implementation_package_id=_text(
                        row, "implementation_package_id"
                    ),
                    commit_sha=_sha_or_blank(
                        row.get("rollback_target_commit_sha"),
                        "rollback_target_commit_sha",
                    ),
                )
            )

    _append_static(
        events,
        rollback_executions,
        label="Execuções de rollback v2.13",
        required={
            "rollback_execution_record_id",
            "rollback_decision_record_id",
            "implementation_package_id",
            "rolled_back_at",
            "rollback_execution_state",
            "rolled_back_commit_sha",
        },
        event_type="rollback_execution",
        id_col="rollback_execution_record_id",
        parent_event_type="rollback_decision",
        parent_col="rollback_decision_record_id",
        state_col="rollback_execution_state",
        event_at_col="rolled_back_at",
        package_col="implementation_package_id",
        commit_col="rolled_back_commit_sha",
    )

    ledger = pd.DataFrame(events)
    if ledger.empty:
        return pd.DataFrame(columns=[
            "event_key",
            "stage_order",
            "event_type",
            "record_id",
            "parent_event_key",
            "parent_event_type",
            "parent_record_id",
            "event_at",
            "state",
            "proposal_id",
            "implementation_package_id",
            "commit_sha",
            "environment",
            "lineage_status",
            "ledger_is_not_execution",
            "ledger_does_not_trigger_actions",
            "automatic_action_enabled",
            "human_review_required",
        ])

    ledger["event_key"] = (
        ledger["event_type"].astype(str)
        + ":"
        + ledger["record_id"].astype(str)
    )
    if ledger["event_key"].duplicated().any():
        dup = ledger.loc[
            ledger["event_key"].duplicated(keep=False),
            "event_key",
        ].tolist()
        raise ValueError(f"event_key duplicado: {dup}")

    stage_order = config["stage_order"]
    unknown_types = set(ledger["event_type"]) - set(stage_order)
    if unknown_types:
        raise ValueError(f"Tipos de evento sem stage_order: {sorted(unknown_types)}")
    ledger["stage_order"] = ledger["event_type"].map(stage_order).astype(int)

    ledger["parent_event_key"] = ledger.apply(
        lambda row: (
            f"{row['parent_event_type']}:{row['parent_record_id']}"
            if row["parent_event_type"] and row["parent_record_id"]
            else ""
        ),
        axis=1,
    )

    allowed_transitions = config["allowed_transitions"]
    keys = set(ledger["event_key"].astype(str))
    for row in ledger.to_dict(orient="records"):
        if row["event_type"] == "proposal":
            if row["parent_event_key"]:
                raise ValueError("Proposal não pode ter parent_event_key.")
            continue

        parent_key = str(row["parent_event_key"])
        if not parent_key or parent_key not in keys:
            raise ValueError(
                f"Evento órfão: {row['event_key']} -> {parent_key or '<vazio>'}"
            )

        allowed_children = set(
            allowed_transitions.get(row["parent_event_type"], [])
        )
        if row["event_type"] not in allowed_children:
            raise ValueError(
                f"Transição não permitida: {row['parent_event_type']} "
                f"-> {row['event_type']}"
            )

    ledger = ledger.sort_values(
        ["stage_order", "event_at", "event_key"],
        kind="stable",
    ).reset_index(drop=True)

    index = {
        row["event_key"]: idx
        for idx, row in ledger.iterrows()
    }

    for idx, row in ledger.iterrows():
        if row["event_type"] == "proposal":
            expected_proposal = str(row["record_id"])
            if row["proposal_id"] and str(row["proposal_id"]) != expected_proposal:
                raise ValueError(
                    f"{row['event_key']}: proposal_id inconsistente."
                )
            ledger.at[idx, "proposal_id"] = expected_proposal
            continue

        parent = ledger.loc[index[row["parent_event_key"]]]
        parent_proposal = str(parent["proposal_id"])
        current_proposal = str(row["proposal_id"]) if row["proposal_id"] else ""
        if current_proposal and current_proposal != parent_proposal:
            raise ValueError(
                f"{row['event_key']}: proposal_id diverge da linhagem pai."
            )
        ledger.at[idx, "proposal_id"] = parent_proposal

        if row["event_type"] == "implementation_package":
            package_id = str(row["record_id"])
            if (
                row["implementation_package_id"]
                and str(row["implementation_package_id"]) != package_id
            ):
                raise ValueError(
                    f"{row['event_key']}: implementation_package_id inconsistente."
                )
            ledger.at[idx, "implementation_package_id"] = package_id
        else:
            parent_package = (
                str(parent["implementation_package_id"])
                if parent["implementation_package_id"]
                else ""
            )
            current_package = (
                str(row["implementation_package_id"])
                if row["implementation_package_id"]
                else ""
            )
            if current_package and parent_package and current_package != parent_package:
                raise ValueError(
                    f"{row['event_key']}: implementation_package_id diverge da linhagem pai."
                )
            ledger.at[idx, "implementation_package_id"] = (
                current_package or parent_package
            )

        if not row["environment"] and parent["environment"]:
            ledger.at[idx, "environment"] = str(parent["environment"])
        elif (
            row["environment"]
            and parent["environment"]
            and str(row["environment"]).lower()
            != str(parent["environment"]).lower()
        ):
            raise ValueError(
                f"{row['event_key']}: ambiente diverge do evento pai."
            )

        if row["event_at"] and parent["event_at"]:
            child_ts = pd.to_datetime(
                row["event_at"], errors="coerce", utc=True
            )
            parent_ts = pd.to_datetime(
                parent["event_at"], errors="coerce", utc=True
            )
            if pd.isna(child_ts) or pd.isna(parent_ts):
                raise ValueError(
                    f"{row['event_key']}: event_at inválido."
                )
            if child_ts < parent_ts:
                raise ValueError(
                    f"{row['event_key']}: cronologia anterior ao evento pai."
                )

    commit_continuity_children = set(
        config["commit_continuity_children"]
    )
    for idx, row in ledger.iterrows():
        if row["event_type"] not in commit_continuity_children:
            continue
        parent = ledger.loc[index[row["parent_event_key"]]]
        child_commit = str(row["commit_sha"]) if row["commit_sha"] else ""
        parent_commit = (
            str(parent["commit_sha"]) if parent["commit_sha"] else ""
        )
        if child_commit and parent_commit and child_commit != parent_commit:
            raise ValueError(
                f"{row['event_key']}: quebra de continuidade de commit "
                f"({parent_commit} -> {child_commit})."
            )

    ledger["lineage_status"] = "linked_and_validated"
    ledger["ledger_is_not_execution"] = True
    ledger["ledger_does_not_trigger_actions"] = True
    ledger["automatic_action_enabled"] = False
    ledger["human_review_required"] = True

    ordered = [
        "event_key",
        "stage_order",
        "event_type",
        "record_id",
        "parent_event_key",
        "parent_event_type",
        "parent_record_id",
        "event_at",
        "state",
        "proposal_id",
        "implementation_package_id",
        "commit_sha",
        "environment",
        "lineage_status",
        "ledger_is_not_execution",
        "ledger_does_not_trigger_actions",
        "automatic_action_enabled",
        "human_review_required",
    ]
    return ledger[ordered].reset_index(drop=True)


def summarize_change_lifecycle_ledger(ledger: pd.DataFrame) -> dict:
    required = {
        "event_key",
        "stage_order",
        "event_type",
        "proposal_id",
        "lineage_status",
        "ledger_is_not_execution",
        "ledger_does_not_trigger_actions",
        "automatic_action_enabled",
    }
    missing = required.difference(ledger.columns)
    if missing:
        raise ValueError(f"Ledger v2.15 sem colunas: {sorted(missing)}")

    if ledger["automatic_action_enabled"].astype(bool).any():
        raise ValueError("Ledger não pode habilitar ação automática.")
    if not ledger["ledger_is_not_execution"].astype(bool).all():
        raise ValueError("Ledger deve permanecer distinto de execução.")
    if not ledger["ledger_does_not_trigger_actions"].astype(bool).all():
        raise ValueError("Ledger não pode disparar ações.")

    summary = {
        "events": int(len(ledger)),
        "proposals": int(ledger["proposal_id"].nunique()),
        "events_by_type": {
            str(k): int(v)
            for k, v in ledger["event_type"]
            .astype("string")
            .value_counts(dropna=False)
            .to_dict()
            .items()
        },
        "lineage_status": "linked_and_validated",
        "orphan_events": 0,
        "automatic_action_enabled": False,
        "ledger_is_not_execution": True,
        "ledger_does_not_trigger_actions": True,
    }

    if not ledger.empty:
        furthest = (
            ledger.sort_values(["proposal_id", "stage_order"])
            .groupby("proposal_id", as_index=False)
            .tail(1)
        )
        summary["furthest_stage_by_proposal"] = {
            str(k): int(v)
            for k, v in furthest["event_type"]
            .astype("string")
            .value_counts(dropna=False)
            .to_dict()
            .items()
        }
    else:
        summary["furthest_stage_by_proposal"] = {}

    return summary
