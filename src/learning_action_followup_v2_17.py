# -*- coding: utf-8 -*-
from __future__ import annotations

import hashlib
import json
import re
from pathlib import Path

import pandas as pd


REQUIRED_ACTION_COLUMNS = {
    "postmortem_record_id",
    "action_sequence",
    "action_description",
    "owner_role",
    "created_at",
    "due_at",
    "action_status",
    "status_updated_at",
    "completed_at",
    "completion_evidence_refs",
    "verification_status",
    "verified_at",
    "verifier_role",
    "verification_notes",
    "blocking_reason",
    "cancellation_rationale",
    "governance_handoff_ref",
}

REQUIRED_POSTMORTEM_COLUMNS = {
    "postmortem_record_id",
    "implementation_package_id",
    "conducted_at",
    "postmortem_status",
    "learning_action_type",
    "follow_up_actions",
    "reenter_rule_review",
    "rule_review_scope",
    "rule_review_reason",
    "postmortem_is_not_causal_proof",
    "learning_is_not_rule_change",
    "rule_reentry_requires_human_review",
    "automatic_rule_change_enabled",
    "automatic_issue_creation_enabled",
}

FORBIDDEN_IDENTIFIER_COLUMNS = {
    "name",
    "nome",
    "cpf",
    "cns",
    "matricula",
    "email",
    "e_mail",
    "telefone",
    "phone",
    "reviewer_name",
    "owner_name",
    "verifier_name",
}

TZ_RE = re.compile(r"(?:Z|[+-]\d{2}:\d{2})$", re.I)


def load_learning_action_followup_config(path: Path) -> dict:
    cfg = json.loads(path.read_text(encoding="utf-8"))
    principles = cfg.get("principles") or {}

    for key in (
        "tracking_is_not_execution",
        "completion_is_not_effectiveness_proof",
        "verification_is_not_epidemiological_effect",
        "overdue_is_not_risk",
        "human_verification_required",
    ):
        if principles.get(key) is not True:
            raise ValueError(f"{key} deve ser true.")

    for key in (
        "automatic_execution",
        "automatic_issue_creation",
        "automatic_rule_change",
        "personal_identifier_storage",
    ):
        if principles.get(key) is not False:
            raise ValueError(f"{key} deve ser false.")

    return cfg


def _blank(value: object) -> bool:
    return value is None or pd.isna(value) or str(value).strip() == ""


def _bool_value(value: object) -> bool:
    if isinstance(value, bool):
        return value
    text = "" if value is None else str(value).strip().lower()
    if text in {"true", "1", "yes", "sim"}:
        return True
    if text in {"false", "0", "no", "nao", "não"}:
        return False
    raise ValueError(f"Valor booleano inválido: {value}")


def _timestamp(
    value: object,
    field: str,
    *,
    required: bool = True,
) -> pd.Timestamp | None:
    if _blank(value):
        if required:
            raise ValueError(f"{field} não pode ser vazio.")
        return None

    text = str(value).strip()
    if not TZ_RE.search(text):
        raise ValueError(f"{field} exige timezone explícito (Z ou ±HH:MM).")

    parsed = pd.to_datetime(text, errors="coerce", utc=True)
    if pd.isna(parsed):
        raise ValueError(f"{field} inválido.")
    return parsed


def _action_record_id(postmortem_record_id: str, sequence: int) -> str:
    basis = f"{postmortem_record_id}|{sequence}"
    return "learning_action_" + hashlib.sha256(
        basis.encode("utf-8")
    ).hexdigest()[:20]


def _source_catalog(
    postmortems: pd.DataFrame,
    config: dict,
) -> dict[str, dict]:
    missing = REQUIRED_POSTMORTEM_COLUMNS.difference(postmortems.columns)
    if missing:
        raise ValueError(
            f"Post-mortem v2.14 sem colunas: {sorted(missing)}"
        )

    eligible_statuses = set(config["eligible_postmortem_statuses"])
    sources: dict[str, dict] = {}

    for row in postmortems.to_dict(orient="records"):
        postmortem_id = str(row["postmortem_record_id"]).strip()
        if not postmortem_id:
            raise ValueError("postmortem_record_id vazio.")

        if str(row["postmortem_status"]).strip() not in eligible_statuses:
            continue

        if not _bool_value(row["postmortem_is_not_causal_proof"]):
            raise ValueError("Fonte v2.14 deve permanecer não causal.")
        if not _bool_value(row["learning_is_not_rule_change"]):
            raise ValueError("Aprendizado v2.14 deve permanecer distinto de mudança.")
        if not _bool_value(row["rule_reentry_requires_human_review"]):
            raise ValueError("Retorno à regra deve exigir revisão humana.")
        if _bool_value(row["automatic_rule_change_enabled"]):
            raise ValueError("Fonte v2.14 não pode habilitar mudança automática de regra.")
        if _bool_value(row["automatic_issue_creation_enabled"]):
            raise ValueError("Fonte v2.14 não pode habilitar criação automática de issue.")

        action_type = str(row["learning_action_type"]).strip()
        if action_type == "none":
            continue

        sources[postmortem_id] = {
            "implementation_package_id": str(
                row["implementation_package_id"]
            ).strip(),
            "conducted_at": _timestamp(
                row["conducted_at"], "conducted_at"
            ),
            "postmortem_status": str(row["postmortem_status"]).strip(),
            "learning_action_type": action_type,
            "follow_up_actions": str(row["follow_up_actions"]).strip(),
            "reenter_rule_review": _bool_value(row["reenter_rule_review"]),
            "rule_review_scope": (
                "" if _blank(row["rule_review_scope"])
                else str(row["rule_review_scope"]).strip()
            ),
            "rule_review_reason": (
                "" if _blank(row["rule_review_reason"])
                else str(row["rule_review_reason"]).strip()
            ),
        }

    return sources


def validate_learning_action_followup(
    records: pd.DataFrame,
    postmortems: pd.DataFrame,
    config: dict,
    as_of: str | pd.Timestamp,
) -> pd.DataFrame:
    missing = REQUIRED_ACTION_COLUMNS.difference(records.columns)
    if missing:
        raise ValueError(
            f"Follow-up v2.17 sem colunas: {sorted(missing)}"
        )

    forbidden = {
        str(col).strip().lower()
        for col in records.columns
    } & FORBIDDEN_IDENTIFIER_COLUMNS
    if forbidden:
        raise ValueError(
            "Colunas de identificadores pessoais não permitidas: "
            + ", ".join(sorted(forbidden))
        )

    as_of_ts = _timestamp(as_of, "as_of")
    assert as_of_ts is not None

    sources = _source_catalog(postmortems, config)
    allowed_statuses = set(config["action_statuses"])
    allowed_verification = set(config["verification_statuses"])

    sequence_numeric = pd.to_numeric(
        records["action_sequence"], errors="coerce"
    )
    if sequence_numeric.isna().any():
        raise ValueError("action_sequence deve ser inteiro positivo.")
    if (sequence_numeric <= 0).any() or (
        sequence_numeric % 1 != 0
    ).any():
        raise ValueError("action_sequence deve ser inteiro positivo.")

    data = records.copy()
    data["action_sequence"] = sequence_numeric.astype(int)

    if data[["postmortem_record_id", "action_sequence"]].duplicated().any():
        raise ValueError(
            "postmortem_record_id + action_sequence deve ser único."
        )

    rows: list[dict] = []

    for row in data.to_dict(orient="records"):
        postmortem_id = str(row["postmortem_record_id"]).strip()
        if postmortem_id not in sources:
            raise ValueError(
                f"Post-mortem inexistente, inelegível ou sem ação: {postmortem_id}"
            )
        source = sources[postmortem_id]

        if _blank(row["action_description"]):
            raise ValueError("action_description não pode ser vazio.")
        if _blank(row["owner_role"]):
            raise ValueError("owner_role não pode ser vazio.")

        status = str(row["action_status"]).strip()
        verification = str(row["verification_status"]).strip()
        if status not in allowed_statuses:
            raise ValueError(f"action_status inválido: {status}")
        if verification not in allowed_verification:
            raise ValueError(
                f"verification_status inválido: {verification}"
            )

        created_at = _timestamp(row["created_at"], "created_at")
        due_at = _timestamp(row["due_at"], "due_at")
        status_updated_at = _timestamp(
            row["status_updated_at"], "status_updated_at"
        )
        assert created_at is not None
        assert due_at is not None
        assert status_updated_at is not None

        if created_at < source["conducted_at"]:
            raise ValueError(
                "created_at não pode ser anterior ao post-mortem."
            )
        if due_at <= created_at:
            raise ValueError("due_at deve ser posterior a created_at.")
        if status_updated_at < created_at:
            raise ValueError(
                "status_updated_at não pode ser anterior a created_at."
            )
        if status_updated_at > as_of_ts:
            raise ValueError(
                "status_updated_at não pode estar no futuro em relação a as_of."
            )

        completed_at = _timestamp(
            row["completed_at"], "completed_at", required=False
        )
        verified_at = _timestamp(
            row["verified_at"], "verified_at", required=False
        )

        evidence = (
            "" if _blank(row["completion_evidence_refs"])
            else str(row["completion_evidence_refs"]).strip()
        )
        verifier_role = (
            "" if _blank(row["verifier_role"])
            else str(row["verifier_role"]).strip()
        )
        verification_notes = (
            "" if _blank(row["verification_notes"])
            else str(row["verification_notes"]).strip()
        )
        blocking_reason = (
            "" if _blank(row["blocking_reason"])
            else str(row["blocking_reason"]).strip()
        )
        cancellation_rationale = (
            "" if _blank(row["cancellation_rationale"])
            else str(row["cancellation_rationale"]).strip()
        )
        handoff_ref = (
            "" if _blank(row["governance_handoff_ref"])
            else str(row["governance_handoff_ref"]).strip()
        )

        if status == "completed":
            if completed_at is None:
                raise ValueError(
                    "action_status=completed exige completed_at."
                )
            if completed_at < created_at or completed_at > status_updated_at:
                raise ValueError(
                    "completed_at deve ficar entre created_at e status_updated_at."
                )
            if not evidence:
                raise ValueError(
                    "action_status=completed exige completion_evidence_refs."
                )
            if verification not in {"pending", "verified", "rejected"}:
                raise ValueError(
                    "Ação concluída exige verificação pending, verified ou rejected."
                )
        else:
            if completed_at is not None or evidence:
                raise ValueError(
                    "completed_at/evidência de conclusão só são permitidos com action_status=completed."
                )

        if verification in {"verified", "rejected"}:
            if status != "completed":
                raise ValueError(
                    "verified/rejected só são permitidos para ação concluída."
                )
            if verified_at is None or not verifier_role or not verification_notes:
                raise ValueError(
                    "verified/rejected exige verified_at, verifier_role e verification_notes."
                )
            assert completed_at is not None
            if verified_at < completed_at or verified_at > as_of_ts:
                raise ValueError(
                    "verified_at deve ser posterior à conclusão e não pode exceder as_of."
                )
        else:
            if verified_at is not None or verifier_role or verification_notes:
                raise ValueError(
                    "Campos de verificação humana só são permitidos com verification_status=verified/rejected."
                )

        if status == "cancelled":
            if verification != "not_applicable":
                raise ValueError(
                    "Ação cancelada exige verification_status=not_applicable."
                )
            if not cancellation_rationale:
                raise ValueError(
                    "Ação cancelada exige cancellation_rationale."
                )
        elif cancellation_rationale:
            raise ValueError(
                "cancellation_rationale só é permitido para ação cancelada."
            )

        if status == "blocked":
            if verification != "not_started":
                raise ValueError(
                    "Ação bloqueada deve manter verification_status=not_started."
                )
            if not blocking_reason:
                raise ValueError(
                    "Ação bloqueada exige blocking_reason."
                )
        elif blocking_reason:
            raise ValueError(
                "blocking_reason só é permitido para ação bloqueada."
            )

        if status in {"planned", "acknowledged", "in_progress"}:
            if verification != "not_started":
                raise ValueError(
                    "Ação aberta deve manter verification_status=not_started."
                )

        if source["learning_action_type"] == "rule_review":
            if source["reenter_rule_review"] is not True:
                raise ValueError(
                    "Ação rule_review exige reenter_rule_review=true na origem."
                )
            if status == "completed" and not handoff_ref:
                raise ValueError(
                    "rule_review concluída exige governance_handoff_ref."
                )
        elif handoff_ref:
            raise ValueError(
                "governance_handoff_ref é reservado para learning_action_type=rule_review."
            )

        active = status in {
            "planned", "acknowledged", "in_progress", "blocked"
        }
        overdue = bool(active and as_of_ts > due_at)

        if status == "cancelled":
            follow_up_state = "cancelled"
        elif status == "blocked":
            follow_up_state = "blocked_overdue" if overdue else "blocked"
        elif status == "completed":
            follow_up_state = {
                "pending": "completed_pending_verification",
                "verified": "verified_closed",
                "rejected": "verification_rejected",
            }[verification]
        else:
            follow_up_state = "overdue" if overdue else "open"

        normalized = {
            "learning_action_record_id": _action_record_id(
                postmortem_id, int(row["action_sequence"])
            ),
            "postmortem_record_id": postmortem_id,
            "implementation_package_id": source[
                "implementation_package_id"
            ],
            "postmortem_status": source["postmortem_status"],
            "learning_action_type": source["learning_action_type"],
            "source_follow_up_actions": source["follow_up_actions"],
            "reenter_rule_review": source["reenter_rule_review"],
            "rule_review_scope": source["rule_review_scope"],
            "rule_review_reason": source["rule_review_reason"],
            "action_sequence": int(row["action_sequence"]),
            "action_description": str(row["action_description"]).strip(),
            "owner_role": str(row["owner_role"]).strip(),
            "created_at": created_at.isoformat(),
            "due_at": due_at.isoformat(),
            "action_status": status,
            "status_updated_at": status_updated_at.isoformat(),
            "completed_at": (
                completed_at.isoformat() if completed_at is not None else ""
            ),
            "completion_evidence_refs": evidence,
            "verification_status": verification,
            "verified_at": (
                verified_at.isoformat() if verified_at is not None else ""
            ),
            "verifier_role": verifier_role,
            "verification_notes": verification_notes,
            "blocking_reason": blocking_reason,
            "cancellation_rationale": cancellation_rationale,
            "governance_handoff_ref": handoff_ref,
            "follow_up_state": follow_up_state,
            "overdue": overdue,
            "as_of": as_of_ts.isoformat(),
            "tracking_is_not_execution": True,
            "completion_is_not_effectiveness_proof": True,
            "verification_is_not_epidemiological_effect": True,
            "overdue_is_not_risk": True,
            "human_verification_required": True,
            "automatic_execution_enabled": False,
            "automatic_issue_creation_enabled": False,
            "automatic_rule_change_enabled": False,
            "personal_identifier_storage": False,
        }
        rows.append(normalized)

    out = pd.DataFrame(rows)
    if out.empty:
        return pd.DataFrame(columns=[
            "learning_action_record_id",
            "postmortem_record_id",
            "implementation_package_id",
            "postmortem_status",
            "learning_action_type",
            "source_follow_up_actions",
            "reenter_rule_review",
            "rule_review_scope",
            "rule_review_reason",
            "action_sequence",
            "action_description",
            "owner_role",
            "created_at",
            "due_at",
            "action_status",
            "status_updated_at",
            "completed_at",
            "completion_evidence_refs",
            "verification_status",
            "verified_at",
            "verifier_role",
            "verification_notes",
            "blocking_reason",
            "cancellation_rationale",
            "governance_handoff_ref",
            "follow_up_state",
            "overdue",
            "as_of",
            "tracking_is_not_execution",
            "completion_is_not_effectiveness_proof",
            "verification_is_not_epidemiological_effect",
            "overdue_is_not_risk",
            "human_verification_required",
            "automatic_execution_enabled",
            "automatic_issue_creation_enabled",
            "automatic_rule_change_enabled",
            "personal_identifier_storage",
        ])

    if out["learning_action_record_id"].duplicated().any():
        raise ValueError("learning_action_record_id duplicado.")

    return out.sort_values(
        ["due_at", "postmortem_record_id", "action_sequence"],
        kind="stable",
    ).reset_index(drop=True)
