# -*- coding: utf-8 -*-
from __future__ import annotations

import pandas as pd


REQUIRED_EVENT_COLUMNS = {
    "decision_record_id",
    "event_at",
    "reviewer_role",
    "follow_up_event_status",
    "follow_up_note",
}


def validate_follow_up_events(
    events: pd.DataFrame,
    decisions: pd.DataFrame,
    allowed_statuses: set[str],
) -> pd.DataFrame:
    missing = REQUIRED_EVENT_COLUMNS.difference(events.columns)
    if missing:
        raise ValueError(
            f"Eventos de follow-up sem colunas: {sorted(missing)}"
        )
    if "decision_record_id" not in decisions.columns:
        raise ValueError("Decisões sem decision_record_id.")

    valid_ids = set(decisions["decision_record_id"].astype(str))
    follow_required = decisions.set_index("decision_record_id")[
        "follow_up_required"
    ].astype(bool)

    data = events.copy()
    if "evidence_refs" not in data.columns:
        data["evidence_refs"] = ""

    parsed_event = pd.to_datetime(
        data["event_at"], errors="coerce", utc=True
    )
    if parsed_event.isna().any():
        raise ValueError("event_at contém data/hora inválida.")
    data["event_at"] = parsed_event.astype("string")

    for row in data.to_dict(orient="records"):
        decision_id = str(row["decision_record_id"]).strip()
        if decision_id not in valid_ids:
            raise ValueError(
                f"Follow-up referencia decisão inexistente: {decision_id}"
            )
        if not bool(follow_required.loc[decision_id]):
            raise ValueError(
                f"{decision_id}: decisão não exige follow-up."
            )
        status = str(row["follow_up_event_status"]).strip()
        if status not in allowed_statuses:
            raise ValueError(f"follow_up_event_status inválido: {status}")
        if not str(row["reviewer_role"]).strip():
            raise ValueError("reviewer_role não pode ser vazio.")
        if not str(row["follow_up_note"]).strip():
            raise ValueError("follow_up_note não pode ser vazio.")

    if data.duplicated(
        ["decision_record_id", "event_at", "follow_up_event_status"]
    ).any():
        raise ValueError("Há evento de follow-up duplicado.")

    data["follow_up_event_recorded_by_human"] = True
    data["automatic_execution_enabled"] = False
    data["follow_up_event_is_not_proof_of_external_action"] = True
    return data.sort_values(
        ["event_at", "decision_record_id"]
    ).reset_index(drop=True)


def build_follow_up_status(
    decisions: pd.DataFrame,
    events: pd.DataFrame | None,
    as_of: str | pd.Timestamp,
) -> pd.DataFrame:
    required = {
        "decision_record_id",
        "codigo_ibge",
        "municipio",
        "decision_status",
        "follow_up_required",
        "follow_up_due_at",
        "follow_up_owner_role",
    }
    missing = required.difference(decisions.columns)
    if missing:
        raise ValueError(f"Decisões sem colunas: {sorted(missing)}")

    as_of_ts = pd.to_datetime(as_of, errors="coerce", utc=True)
    if pd.isna(as_of_ts):
        raise ValueError("as_of inválido.")

    latest_event = {}
    if events is not None and not events.empty:
        ordered = events.copy()
        ordered["_event_ts"] = pd.to_datetime(
            ordered["event_at"], errors="coerce", utc=True
        )
        ordered = ordered.sort_values(
            ["decision_record_id", "_event_ts"]
        )
        latest_event = {
            key: group.iloc[-1].to_dict()
            for key, group in ordered.groupby("decision_record_id")
        }

    rows = []
    for row in decisions.to_dict(orient="records"):
        decision_id = str(row["decision_record_id"])
        required_follow = bool(row["follow_up_required"])
        event = latest_event.get(decision_id)

        if not required_follow:
            state = "not_required"
            latest_status = ""
            latest_event_at = ""
        elif event is not None and str(
            event["follow_up_event_status"]
        ) == "completed":
            state = "completed"
            latest_status = "completed"
            latest_event_at = str(event["event_at"])
        elif event is not None and str(
            event["follow_up_event_status"]
        ) == "cancelled":
            state = "cancelled"
            latest_status = "cancelled"
            latest_event_at = str(event["event_at"])
        else:
            due = pd.to_datetime(
                row["follow_up_due_at"], errors="coerce", utc=True
            )
            if pd.isna(due):
                raise ValueError(
                    f"{decision_id}: follow-up requerido sem prazo válido."
                )
            if as_of_ts > due:
                state = "overdue"
            else:
                state = "open"
            latest_status = (
                str(event["follow_up_event_status"])
                if event is not None else ""
            )
            latest_event_at = (
                str(event["event_at"]) if event is not None else ""
            )

        rows.append({
            "decision_record_id": decision_id,
            "codigo_ibge": row["codigo_ibge"],
            "municipio": row["municipio"],
            "decision_status": row["decision_status"],
            "follow_up_required": required_follow,
            "follow_up_due_at": row["follow_up_due_at"],
            "follow_up_owner_role": row["follow_up_owner_role"],
            "latest_follow_up_event_status": latest_status,
            "latest_follow_up_event_at": latest_event_at,
            "follow_up_state": state,
            "as_of": str(as_of_ts),
            "automatic_execution_enabled": False,
            "follow_up_state_is_not_risk": True,
            "human_review_required": True,
        })

    return pd.DataFrame(rows).sort_values(
        ["follow_up_state", "municipio", "decision_record_id"]
    ).reset_index(drop=True)
