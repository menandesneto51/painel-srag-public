# -*- coding: utf-8 -*-
from __future__ import annotations

import hashlib
import json
from pathlib import Path

import pandas as pd


REQUIRED_COLUMNS = {
    "source_record_type",
    "source_record_id",
    "conducted_at",
    "reviewer_role",
    "postmortem_status",
    "outcome_state",
    "event_summary",
    "expected_behavior_summary",
    "observed_behavior_summary",
    "contributing_factors",
    "safeguards_that_worked",
    "safeguards_to_improve",
    "lessons_learned",
    "learning_action_type",
    "follow_up_actions",
    "evidence_refs",
    "reenter_rule_review",
    "rule_review_scope",
    "rule_review_reason",
}


def load_postmortem_config(path: Path) -> dict:
    cfg = json.loads(path.read_text(encoding="utf-8"))
    principles = cfg.get("principles") or {}

    for key in (
        "postmortem_is_not_causal_proof",
        "learning_is_not_rule_change",
        "rule_reentry_requires_human_review",
    ):
        if principles.get(key) is not True:
            raise ValueError(f"{key} deve ser true.")

    for key in (
        "automatic_rule_change",
        "automatic_issue_creation",
        "automatic_deploy",
        "automatic_rollback",
        "patient_level_decision",
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


def _record_id(
    source_type: str,
    source_id: str,
    conducted_at: str,
    outcome_state: str,
) -> str:
    basis = f"{source_type}|{source_id}|{conducted_at}|{outcome_state}"
    return "postmortem_" + hashlib.sha256(
        basis.encode("utf-8")
    ).hexdigest()[:20]


def _source_catalog(
    effects: pd.DataFrame | None,
    rollbacks: pd.DataFrame | None,
) -> dict[tuple[str, str], dict]:
    sources: dict[tuple[str, str], dict] = {}

    if effects is not None and not effects.empty:
        required = {
            "effect_verification_record_id",
            "deployment_record_id",
            "implementation_package_id",
            "deployed_commit_sha",
            "effect_state",
            "effect_verification_is_not_causal_inference",
            "automatic_rule_change_enabled",
            "automatic_rollback_enabled",
        }
        missing = required.difference(effects.columns)
        if missing:
            raise ValueError(
                f"Efeitos v2.12 sem colunas: {sorted(missing)}"
            )

        for row in effects.to_dict(orient="records"):
            if not _bool_value(
                row["effect_verification_is_not_causal_inference"]
            ):
                raise ValueError(
                    "Verificação v2.12 deve permanecer não causal."
                )
            if _bool_value(row["automatic_rule_change_enabled"]):
                raise ValueError(
                    "Fonte v2.12 não pode habilitar mudança automática de regra."
                )
            if _bool_value(row["automatic_rollback_enabled"]):
                raise ValueError(
                    "Fonte v2.12 não pode habilitar rollback automático."
                )

            sources[
                ("effect", str(row["effect_verification_record_id"]))
            ] = {
                "implementation_package_id": str(
                    row["implementation_package_id"]
                ),
                "source_state": str(row["effect_state"]),
                "technical_commit_sha": str(row["deployed_commit_sha"]),
                "related_record_id": str(row["deployment_record_id"]),
            }

    if rollbacks is not None and not rollbacks.empty:
        required = {
            "rollback_execution_record_id",
            "implementation_package_id",
            "rolled_back_commit_sha",
            "rollback_execution_state",
            "rollback_record_requires_actual_rollback_evidence",
            "automatic_rule_change_enabled",
            "automatic_rollback_enabled",
        }
        missing = required.difference(rollbacks.columns)
        if missing:
            raise ValueError(
                f"Rollbacks v2.13 sem colunas: {sorted(missing)}"
            )

        for row in rollbacks.to_dict(orient="records"):
            if not _bool_value(
                row["rollback_record_requires_actual_rollback_evidence"]
            ):
                raise ValueError(
                    "Rollback v2.13 deve exigir evidência real."
                )
            if _bool_value(row["automatic_rule_change_enabled"]):
                raise ValueError(
                    "Fonte v2.13 não pode habilitar mudança automática de regra."
                )
            if _bool_value(row["automatic_rollback_enabled"]):
                raise ValueError(
                    "Fonte v2.13 não pode habilitar rollback automático."
                )

            sources[
                ("rollback", str(row["rollback_execution_record_id"]))
            ] = {
                "implementation_package_id": str(
                    row["implementation_package_id"]
                ),
                "source_state": str(row["rollback_execution_state"]),
                "technical_commit_sha": str(row["rolled_back_commit_sha"]),
                "related_record_id": "",
            }

    return sources


def validate_postmortem_records(
    records: pd.DataFrame,
    effects: pd.DataFrame | None,
    rollbacks: pd.DataFrame | None,
    config: dict,
) -> pd.DataFrame:
    missing = REQUIRED_COLUMNS.difference(records.columns)
    if missing:
        raise ValueError(
            f"Post-mortem v2.14 sem colunas: {sorted(missing)}"
        )

    sources = _source_catalog(effects, rollbacks)

    allowed_source_types = set(config["source_record_types"])
    allowed_statuses = set(config["postmortem_statuses"])
    allowed_outcomes = set(config["outcome_states"])
    allowed_actions = set(config["learning_action_types"])
    allowed_scopes = set(config["rule_review_scopes"])

    data = records.copy()
    parsed = pd.to_datetime(
        data["conducted_at"], errors="coerce", utc=True
    )
    if parsed.isna().any():
        raise ValueError("conducted_at contém data/hora inválida.")
    data["conducted_at"] = parsed.astype("string")

    rows = []
    for row in data.to_dict(orient="records"):
        source_type = str(row["source_record_type"]).strip()
        source_id = str(row["source_record_id"]).strip()

        if source_type not in allowed_source_types:
            raise ValueError(
                f"source_record_type inválido: {source_type}"
            )
        key = (source_type, source_id)
        if key not in sources:
            raise ValueError(
                f"Fonte v2.14 inexistente ou não validada: {source_type}:{source_id}"
            )
        source = sources[key]

        status = str(row["postmortem_status"]).strip()
        outcome = str(row["outcome_state"]).strip()
        action = str(row["learning_action_type"]).strip()

        if status not in allowed_statuses:
            raise ValueError(f"postmortem_status inválido: {status}")
        if outcome not in allowed_outcomes:
            raise ValueError(f"outcome_state inválido: {outcome}")
        if action not in allowed_actions:
            raise ValueError(
                f"learning_action_type inválido: {action}"
            )

        for field in (
            "reviewer_role",
            "event_summary",
            "expected_behavior_summary",
            "observed_behavior_summary",
            "contributing_factors",
            "safeguards_that_worked",
            "safeguards_to_improve",
            "lessons_learned",
            "follow_up_actions",
            "evidence_refs",
        ):
            if _blank(row.get(field)):
                raise ValueError(f"{field} não pode ser vazio.")

        reenter = _bool_value(row["reenter_rule_review"])
        scope = "" if _blank(row["rule_review_scope"]) else str(
            row["rule_review_scope"]
        ).strip()
        reason = "" if _blank(row["rule_review_reason"]) else str(
            row["rule_review_reason"]
        ).strip()

        if reenter:
            if action != "rule_review":
                raise ValueError(
                    "reenter_rule_review=true exige learning_action_type=rule_review."
                )
            if scope not in allowed_scopes:
                raise ValueError(
                    "reenter_rule_review=true exige rule_review_scope válido."
                )
            if not reason:
                raise ValueError(
                    "reenter_rule_review=true exige rule_review_reason."
                )
        else:
            if action == "rule_review":
                raise ValueError(
                    "learning_action_type=rule_review exige reenter_rule_review=true."
                )
            if scope or reason:
                raise ValueError(
                    "rule_review_scope/reason devem ficar vazios quando reenter_rule_review=false."
                )

        if status == "closed" and outcome == "investigation_open":
            raise ValueError(
                "Post-mortem fechado não pode manter outcome_state=investigation_open."
            )

        normalized = dict(row)
        normalized["implementation_package_id"] = source[
            "implementation_package_id"
        ]
        normalized["source_state"] = source["source_state"]
        normalized["technical_commit_sha"] = source[
            "technical_commit_sha"
        ]
        normalized["related_record_id"] = source[
            "related_record_id"
        ]
        normalized["reenter_rule_review"] = reenter
        normalized["postmortem_record_id"] = _record_id(
            source_type,
            source_id,
            normalized["conducted_at"],
            outcome,
        )
        normalized["postmortem_is_not_causal_proof"] = True
        normalized["learning_is_not_rule_change"] = True
        normalized["rule_reentry_requires_human_review"] = True
        normalized["automatic_rule_change_enabled"] = False
        normalized["automatic_issue_creation_enabled"] = False
        normalized["automatic_deploy_enabled"] = False
        normalized["automatic_rollback_enabled"] = False
        normalized["patient_level_decision_enabled"] = False
        normalized["personal_identifier_storage"] = False
        normalized["learning_status"] = "human_postmortem_learning_record"
        rows.append(normalized)

    out = pd.DataFrame(rows)
    if out["postmortem_record_id"].duplicated().any():
        raise ValueError("postmortem_record_id duplicado.")

    ordered = [
        "postmortem_record_id",
        "source_record_type",
        "source_record_id",
        "related_record_id",
        "implementation_package_id",
        "source_state",
        "technical_commit_sha",
        "conducted_at",
        "reviewer_role",
        "postmortem_status",
        "outcome_state",
        "event_summary",
        "expected_behavior_summary",
        "observed_behavior_summary",
        "contributing_factors",
        "safeguards_that_worked",
        "safeguards_to_improve",
        "lessons_learned",
        "learning_action_type",
        "follow_up_actions",
        "evidence_refs",
        "reenter_rule_review",
        "rule_review_scope",
        "rule_review_reason",
        "postmortem_is_not_causal_proof",
        "learning_is_not_rule_change",
        "rule_reentry_requires_human_review",
        "automatic_rule_change_enabled",
        "automatic_issue_creation_enabled",
        "automatic_deploy_enabled",
        "automatic_rollback_enabled",
        "patient_level_decision_enabled",
        "personal_identifier_storage",
        "learning_status",
    ]
    return out[ordered].sort_values(
        ["conducted_at", "source_record_type", "source_record_id"]
    ).reset_index(drop=True)
