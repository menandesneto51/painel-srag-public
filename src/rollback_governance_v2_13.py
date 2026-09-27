# -*- coding: utf-8 -*-
from __future__ import annotations

import hashlib
import json
import re
from pathlib import Path

import pandas as pd


REQUIRED_DECISION_COLUMNS = {
    "source_record_type",
    "source_record_id",
    "decided_at",
    "reviewer_role",
    "rollback_target_commit_sha",
    "rollback_plan_ref",
    "rollback_decision",
    "decision_rationale",
}

REQUIRED_EXECUTION_COLUMNS = {
    "rollback_decision_record_id",
    "rolled_back_at",
    "reviewer_role",
    "rolled_back_commit_sha",
    "rollback_evidence_ref",
    "post_rollback_ci_status",
    "smoke_test_status",
    "health_check_status",
    "security_privacy_check_status",
    "epidemiology_sanity_status",
    "rollback_execution_state",
    "verification_notes",
}


def load_rollback_config(path: Path) -> dict:
    cfg = json.loads(path.read_text(encoding="utf-8"))
    principles = cfg.get("principles") or {}

    for key in (
        "rollback_decision_is_not_rollback_execution",
        "rollback_record_requires_actual_rollback_evidence",
        "human_rollback_required",
        "human_post_rollback_verification_required",
    ):
        if principles.get(key) is not True:
            raise ValueError(f"{key} deve ser true.")

    for key in (
        "automatic_rollback",
        "automatic_deploy",
        "automatic_rule_change",
        "patient_level_decision",
        "personal_identifier_storage",
    ):
        if principles.get(key) is not False:
            raise ValueError(f"{key} deve ser false.")

    return cfg


def _blank(value: object) -> bool:
    return value is None or pd.isna(value) or str(value).strip() == ""


def _sha(value: object, field: str) -> str:
    text = "" if value is None else str(value).strip().lower()
    if not re.fullmatch(r"[0-9a-f]{40}", text):
        raise ValueError(
            f"{field} deve ser SHA Git completo de 40 caracteres hexadecimais."
        )
    return text


def _record_id(prefix: str, *values: object) -> str:
    basis = "|".join(str(v) for v in values)
    return prefix + hashlib.sha256(basis.encode("utf-8")).hexdigest()[:20]


def _eligible_sources(
    deployments: pd.DataFrame,
    effects: pd.DataFrame | None,
    config: dict,
) -> dict[tuple[str, str], dict]:
    sources: dict[tuple[str, str], dict] = {}

    required_deploy = {
        "deployment_record_id",
        "implementation_package_id",
        "deployed_commit_sha",
        "deployment_state",
        "automatic_rollback_enabled",
    }
    missing_deploy = required_deploy.difference(deployments.columns)
    if missing_deploy:
        raise ValueError(
            f"Deploys v2.12 sem colunas: {sorted(missing_deploy)}"
        )

    eligible_deploy_states = set(config["eligible_deployment_states"])
    for row in deployments.to_dict(orient="records"):
        if bool(row["automatic_rollback_enabled"]):
            raise ValueError("Fonte v2.12 não pode habilitar rollback automático.")
        if str(row["deployment_state"]).strip() in eligible_deploy_states:
            sources[("deployment", str(row["deployment_record_id"]))] = {
                "implementation_package_id": str(row["implementation_package_id"]),
                "deployed_commit_sha": _sha(
                    row["deployed_commit_sha"], "deployed_commit_sha"
                ),
                "source_state": str(row["deployment_state"]).strip(),
            }

    if effects is not None and not effects.empty:
        required_effect = {
            "effect_verification_record_id",
            "deployment_record_id",
            "implementation_package_id",
            "deployed_commit_sha",
            "effect_state",
            "automatic_rollback_enabled",
            "effect_verification_is_not_causal_inference",
        }
        missing_effect = required_effect.difference(effects.columns)
        if missing_effect:
            raise ValueError(
                f"Efeitos v2.12 sem colunas: {sorted(missing_effect)}"
            )

        eligible_effect_states = set(config["eligible_effect_states"])
        for row in effects.to_dict(orient="records"):
            if bool(row["automatic_rollback_enabled"]):
                raise ValueError("Efeito v2.12 não pode habilitar rollback automático.")
            if not bool(row["effect_verification_is_not_causal_inference"]):
                raise ValueError(
                    "Verificação de efeito deve permanecer não causal."
                )
            if str(row["effect_state"]).strip() in eligible_effect_states:
                sources[
                    ("effect", str(row["effect_verification_record_id"]))
                ] = {
                    "implementation_package_id": str(
                        row["implementation_package_id"]
                    ),
                    "deployed_commit_sha": _sha(
                        row["deployed_commit_sha"], "deployed_commit_sha"
                    ),
                    "source_state": str(row["effect_state"]).strip(),
                    "deployment_record_id": str(row["deployment_record_id"]),
                }

    return sources


def validate_human_rollback_decisions(
    decisions: pd.DataFrame,
    deployments: pd.DataFrame,
    effects: pd.DataFrame | None,
    config: dict,
) -> pd.DataFrame:
    missing = REQUIRED_DECISION_COLUMNS.difference(decisions.columns)
    if missing:
        raise ValueError(
            f"Decisões de rollback v2.13 sem colunas: {sorted(missing)}"
        )

    sources = _eligible_sources(deployments, effects, config)
    allowed_decisions = set(config["rollback_decisions"])

    data = decisions.copy()
    parsed = pd.to_datetime(data["decided_at"], errors="coerce", utc=True)
    if parsed.isna().any():
        raise ValueError("decided_at contém data/hora inválida.")
    data["decided_at"] = parsed.astype("string")

    rows = []
    for row in data.to_dict(orient="records"):
        source_type = str(row["source_record_type"]).strip()
        source_id = str(row["source_record_id"]).strip()
        key = (source_type, source_id)
        if key not in sources:
            raise ValueError(
                f"Fonte não elegível para rollback: {source_type}:{source_id}"
            )
        origin = sources[key]

        decision = str(row["rollback_decision"]).strip()
        if decision not in allowed_decisions:
            raise ValueError(f"rollback_decision inválida: {decision}")

        for field in (
            "reviewer_role",
            "rollback_plan_ref",
            "decision_rationale",
        ):
            if _blank(row.get(field)):
                raise ValueError(f"{field} não pode ser vazio.")

        target_sha = _sha(
            row["rollback_target_commit_sha"],
            "rollback_target_commit_sha",
        )
        deployed_sha = origin["deployed_commit_sha"]
        if target_sha == deployed_sha:
            raise ValueError(
                "rollback_target_commit_sha deve diferir do commit atualmente implantado."
            )

        normalized = dict(row)
        normalized["implementation_package_id"] = origin[
            "implementation_package_id"
        ]
        normalized["deployed_commit_sha"] = deployed_sha
        normalized["source_state"] = origin["source_state"]
        normalized["rollback_target_commit_sha"] = target_sha
        normalized["rollback_decision_record_id"] = _record_id(
            "rollbackdec_",
            source_type,
            source_id,
            normalized["decided_at"],
            decision,
            target_sha,
        )
        normalized["rollback_decision_is_not_rollback_execution"] = True
        normalized["automatic_rollback_enabled"] = False
        normalized["automatic_deploy_enabled"] = False
        normalized["automatic_rule_change_enabled"] = False
        normalized["patient_level_decision_enabled"] = False
        normalized["human_rollback_required"] = True
        normalized["personal_identifier_storage"] = False
        normalized["decision_status"] = "human_rollback_decision_record"
        rows.append(normalized)

    out = pd.DataFrame(rows)
    if out["rollback_decision_record_id"].duplicated().any():
        raise ValueError("rollback_decision_record_id duplicado.")
    return out.sort_values(
        ["decided_at", "source_record_type", "source_record_id"]
    ).reset_index(drop=True)


def validate_rollback_execution_records(
    records: pd.DataFrame,
    decisions: pd.DataFrame,
    config: dict,
) -> pd.DataFrame:
    missing = REQUIRED_EXECUTION_COLUMNS.difference(records.columns)
    if missing:
        raise ValueError(
            f"Registros de rollback v2.13 sem colunas: {sorted(missing)}"
        )

    required_decision = {
        "rollback_decision_record_id",
        "implementation_package_id",
        "rollback_target_commit_sha",
        "rollback_decision",
        "rollback_decision_is_not_rollback_execution",
        "automatic_rollback_enabled",
    }
    missing_decision = required_decision.difference(decisions.columns)
    if missing_decision:
        raise ValueError(
            f"Decisões de rollback sem colunas: {sorted(missing_decision)}"
        )

    decision_data = decisions.copy()
    if decision_data["rollback_decision_record_id"].duplicated().any():
        raise ValueError("rollback_decision_record_id duplicado.")
    lookup = decision_data.set_index("rollback_decision_record_id")

    verification = set(config["verification_statuses"])
    execution_states = set(config["rollback_execution_states"])

    data = records.copy()
    parsed = pd.to_datetime(
        data["rolled_back_at"], errors="coerce", utc=True
    )
    if parsed.isna().any():
        raise ValueError("rolled_back_at contém data/hora inválida.")
    data["rolled_back_at"] = parsed.astype("string")

    rows = []
    for row in data.to_dict(orient="records"):
        decision_id = str(row["rollback_decision_record_id"]).strip()
        if decision_id not in lookup.index:
            raise ValueError(
                f"rollback_decision_record_id inexistente: {decision_id}"
            )
        origin = lookup.loc[decision_id]

        if str(origin["rollback_decision"]).strip() != "approve_human_rollback":
            raise ValueError(
                f"{decision_id}: somente approve_human_rollback pode originar rollback."
            )
        if not bool(origin["rollback_decision_is_not_rollback_execution"]):
            raise ValueError(
                "Decisão de rollback deve permanecer distinta de execução."
            )
        if bool(origin["automatic_rollback_enabled"]):
            raise ValueError("Rollback automático não pode estar habilitado.")

        rolled_back_sha = _sha(
            row["rolled_back_commit_sha"],
            "rolled_back_commit_sha",
        )
        target_sha = _sha(
            origin["rollback_target_commit_sha"],
            "rollback_target_commit_sha",
        )
        if rolled_back_sha != target_sha:
            raise ValueError(
                "rolled_back_commit_sha deve corresponder ao alvo aprovado."
            )

        for field in (
            "post_rollback_ci_status",
            "smoke_test_status",
            "health_check_status",
            "security_privacy_check_status",
            "epidemiology_sanity_status",
        ):
            status = str(row[field]).strip()
            if status not in verification:
                raise ValueError(f"{field} inválido: {status}")

        state = str(row["rollback_execution_state"]).strip()
        if state not in execution_states:
            raise ValueError(
                f"rollback_execution_state inválido: {state}"
            )

        for field in (
            "reviewer_role",
            "rollback_evidence_ref",
            "verification_notes",
        ):
            if _blank(row.get(field)):
                raise ValueError(f"{field} não pode ser vazio.")

        if state == "verified_restored":
            failed = [
                field for field in (
                    "post_rollback_ci_status",
                    "smoke_test_status",
                    "health_check_status",
                    "security_privacy_check_status",
                    "epidemiology_sanity_status",
                )
                if str(row[field]).strip() != "passed"
            ]
            if failed:
                raise ValueError(
                    f"{decision_id}: verified_restored bloqueado; checks não aprovados: {failed}"
                )

        normalized = dict(row)
        normalized["implementation_package_id"] = str(
            origin["implementation_package_id"]
        )
        normalized["rollback_target_commit_sha"] = target_sha
        normalized["rolled_back_commit_sha"] = rolled_back_sha
        normalized["rollback_execution_record_id"] = _record_id(
            "rollback_",
            decision_id,
            rolled_back_sha,
            normalized["rolled_back_at"],
        )
        normalized["rollback_record_requires_actual_rollback_evidence"] = True
        normalized["automatic_rollback_enabled"] = False
        normalized["automatic_deploy_enabled"] = False
        normalized["automatic_rule_change_enabled"] = False
        normalized["patient_level_decision_enabled"] = False
        normalized["human_post_rollback_verification_required"] = True
        normalized["personal_identifier_storage"] = False
        normalized["rollback_record_status"] = "human_post_rollback_verification_record"
        rows.append(normalized)

    out = pd.DataFrame(rows)
    if out["rollback_execution_record_id"].duplicated().any():
        raise ValueError("rollback_execution_record_id duplicado.")
    return out.sort_values(
        ["rolled_back_at", "rollback_decision_record_id"]
    ).reset_index(drop=True)
