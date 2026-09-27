# -*- coding: utf-8 -*-
from __future__ import annotations

import hashlib
import json
import re
from pathlib import Path

import pandas as pd


REQUIRED_DEPLOY_DECISION_COLUMNS = {
    "post_merge_record_id",
    "decided_at",
    "reviewer_role",
    "deploy_decision",
    "decision_rationale",
}

REQUIRED_DEPLOYMENT_COLUMNS = {
    "deploy_decision_record_id",
    "deployed_at",
    "reviewer_role",
    "environment",
    "deployed_commit_sha",
    "deploy_evidence_ref",
    "post_deploy_ci_status",
    "smoke_test_status",
    "health_check_status",
    "security_privacy_check_status",
    "rollback_readiness_status",
    "deployment_state",
    "deployment_notes",
}

REQUIRED_EFFECT_COLUMNS = {
    "deployment_record_id",
    "measured_at",
    "reviewer_role",
    "observation_window_start",
    "observation_window_end",
    "effect_state",
    "expected_behavior_summary",
    "observed_behavior_summary",
    "evidence_refs",
    "effect_review_notes",
}


def load_deployment_config(path: Path) -> dict:
    cfg = json.loads(path.read_text(encoding="utf-8"))
    principles = cfg.get("principles") or {}
    for key in (
        "deploy_decision_is_not_deploy_execution",
        "deployment_record_requires_actual_deploy_evidence",
        "effect_verification_is_not_causal_inference",
        "human_deploy_required",
        "human_effect_review_required",
    ):
        if principles.get(key) is not True:
            raise ValueError(f"{key} deve ser true.")

    for key in (
        "automatic_deploy",
        "automatic_rollback",
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


def validate_human_deploy_decisions(
    decisions: pd.DataFrame,
    post_merge_records: pd.DataFrame,
    config: dict,
) -> pd.DataFrame:
    missing = REQUIRED_DEPLOY_DECISION_COLUMNS.difference(decisions.columns)
    if missing:
        raise ValueError(
            f"Decisões de deploy v2.12 sem colunas: {sorted(missing)}"
        )

    required_source = {
        "post_merge_record_id",
        "implementation_package_id",
        "merged_commit_sha",
        "post_merge_state",
        "post_merge_record_is_not_deploy",
        "automatic_deploy_enabled",
        "automatic_rollback_enabled",
    }
    missing_source = required_source.difference(post_merge_records.columns)
    if missing_source:
        raise ValueError(
            f"Pós-merge v2.11 sem colunas: {sorted(missing_source)}"
        )

    source = post_merge_records.copy()
    if source["post_merge_record_id"].duplicated().any():
        raise ValueError("post_merge_record_id duplicado.")
    lookup = source.set_index("post_merge_record_id")

    allowed_source_states = set(config["allowed_post_merge_states"])
    allowed_decisions = set(config["deploy_decisions"])

    data = decisions.copy()
    parsed = pd.to_datetime(data["decided_at"], errors="coerce", utc=True)
    if parsed.isna().any():
        raise ValueError("decided_at contém data/hora inválida.")
    data["decided_at"] = parsed.astype("string")

    rows = []
    for row in data.to_dict(orient="records"):
        source_id = str(row["post_merge_record_id"]).strip()
        if source_id not in lookup.index:
            raise ValueError(
                f"post_merge_record_id inexistente: {source_id}"
            )
        origin = lookup.loc[source_id]

        if str(origin["post_merge_state"]).strip() not in allowed_source_states:
            raise ValueError(
                f"{source_id}: pós-merge não está apto para decisão de deploy."
            )
        if not bool(origin["post_merge_record_is_not_deploy"]):
            raise ValueError(
                f"{source_id}: registro pós-merge deve permanecer distinto de deploy."
            )
        if bool(origin["automatic_deploy_enabled"]):
            raise ValueError(
                f"{source_id}: deploy automático não pode estar habilitado."
            )
        if bool(origin["automatic_rollback_enabled"]):
            raise ValueError(
                f"{source_id}: rollback automático não pode estar habilitado."
            )

        decision = str(row["deploy_decision"]).strip()
        if decision not in allowed_decisions:
            raise ValueError(f"deploy_decision inválida: {decision}")
        if _blank(row.get("reviewer_role")):
            raise ValueError("reviewer_role não pode ser vazio.")
        if _blank(row.get("decision_rationale")):
            raise ValueError("decision_rationale não pode ser vazio.")

        merged_sha = _sha(origin["merged_commit_sha"], "merged_commit_sha")

        normalized = dict(row)
        normalized["implementation_package_id"] = str(
            origin["implementation_package_id"]
        )
        normalized["merged_commit_sha"] = merged_sha
        normalized["deploy_decision_record_id"] = _record_id(
            "deploydec_",
            source_id,
            normalized["decided_at"],
            decision,
        )
        normalized["deploy_decision_is_not_deploy_execution"] = True
        normalized["automatic_deploy_enabled"] = False
        normalized["automatic_rollback_enabled"] = False
        normalized["human_deploy_required"] = True
        normalized["personal_identifier_storage"] = False
        normalized["decision_status"] = "human_deploy_decision_record"
        rows.append(normalized)

    out = pd.DataFrame(rows)
    if out["deploy_decision_record_id"].duplicated().any():
        raise ValueError("deploy_decision_record_id duplicado.")
    return out.sort_values(
        ["decided_at", "post_merge_record_id"]
    ).reset_index(drop=True)


def validate_deployment_records(
    records: pd.DataFrame,
    deploy_decisions: pd.DataFrame,
    config: dict,
) -> pd.DataFrame:
    missing = REQUIRED_DEPLOYMENT_COLUMNS.difference(records.columns)
    if missing:
        raise ValueError(
            f"Registros de deploy v2.12 sem colunas: {sorted(missing)}"
        )

    required_decision = {
        "deploy_decision_record_id",
        "implementation_package_id",
        "merged_commit_sha",
        "deploy_decision",
        "deploy_decision_is_not_deploy_execution",
        "automatic_deploy_enabled",
        "automatic_rollback_enabled",
    }
    missing_decision = required_decision.difference(deploy_decisions.columns)
    if missing_decision:
        raise ValueError(
            f"Decisões de deploy sem colunas: {sorted(missing_decision)}"
        )

    decisions = deploy_decisions.copy()
    if decisions["deploy_decision_record_id"].duplicated().any():
        raise ValueError("deploy_decision_record_id duplicado.")
    lookup = decisions.set_index("deploy_decision_record_id")

    verification = set(config["verification_statuses"])
    deployment_states = set(config["deployment_states"])

    data = records.copy()
    parsed = pd.to_datetime(data["deployed_at"], errors="coerce", utc=True)
    if parsed.isna().any():
        raise ValueError("deployed_at contém data/hora inválida.")
    data["deployed_at"] = parsed.astype("string")

    rows = []
    for row in data.to_dict(orient="records"):
        decision_id = str(row["deploy_decision_record_id"]).strip()
        if decision_id not in lookup.index:
            raise ValueError(
                f"deploy_decision_record_id inexistente: {decision_id}"
            )
        origin = lookup.loc[decision_id]

        if str(origin["deploy_decision"]).strip() != "approve_human_deploy":
            raise ValueError(
                f"{decision_id}: somente approve_human_deploy pode originar deploy."
            )
        if not bool(origin["deploy_decision_is_not_deploy_execution"]):
            raise ValueError(
                f"{decision_id}: decisão deve permanecer distinta de execução."
            )
        if bool(origin["automatic_deploy_enabled"]):
            raise ValueError("Deploy automático não pode estar habilitado.")
        if bool(origin["automatic_rollback_enabled"]):
            raise ValueError("Rollback automático não pode estar habilitado.")

        deployed_sha = _sha(
            row["deployed_commit_sha"], "deployed_commit_sha"
        )
        merged_sha = _sha(origin["merged_commit_sha"], "merged_commit_sha")
        if deployed_sha != merged_sha:
            raise ValueError(
                f"{decision_id}: deployed_commit_sha deve corresponder ao merged_commit_sha."
            )

        for field in (
            "post_deploy_ci_status",
            "smoke_test_status",
            "health_check_status",
            "security_privacy_check_status",
        ):
            status = str(row[field]).strip()
            if status not in verification:
                raise ValueError(f"{field} inválido: {status}")

        state = str(row["deployment_state"]).strip()
        if state not in deployment_states:
            raise ValueError(f"deployment_state inválido: {state}")

        for field in (
            "reviewer_role",
            "environment",
            "deploy_evidence_ref",
            "rollback_readiness_status",
            "deployment_notes",
        ):
            if _blank(row.get(field)):
                raise ValueError(f"{field} não pode ser vazio.")

        if state == "verified_healthy":
            failed = [
                field for field in (
                    "post_deploy_ci_status",
                    "smoke_test_status",
                    "health_check_status",
                    "security_privacy_check_status",
                )
                if str(row[field]).strip() != "passed"
            ]
            if failed:
                raise ValueError(
                    f"{decision_id}: verified_healthy bloqueado; checks não aprovados: {failed}"
                )
            if str(row["rollback_readiness_status"]).strip() != "ready":
                raise ValueError(
                    "verified_healthy exige rollback_readiness_status=ready."
                )

        normalized = dict(row)
        normalized["implementation_package_id"] = str(
            origin["implementation_package_id"]
        )
        normalized["merged_commit_sha"] = merged_sha
        normalized["deployed_commit_sha"] = deployed_sha
        normalized["deployment_record_id"] = _record_id(
            "deploy_",
            decision_id,
            deployed_sha,
            normalized["deployed_at"],
            normalized["environment"],
        )
        normalized["deployment_record_requires_actual_deploy_evidence"] = True
        normalized["automatic_deploy_enabled"] = False
        normalized["automatic_rollback_enabled"] = False
        normalized["deployment_is_not_effect_verification"] = True
        normalized["human_effect_review_required"] = True
        normalized["personal_identifier_storage"] = False
        rows.append(normalized)

    out = pd.DataFrame(rows)
    if out["deployment_record_id"].duplicated().any():
        raise ValueError("deployment_record_id duplicado.")
    return out.sort_values(
        ["deployed_at", "deploy_decision_record_id"]
    ).reset_index(drop=True)


def validate_effect_verification_records(
    records: pd.DataFrame,
    deployments: pd.DataFrame,
    config: dict,
) -> pd.DataFrame:
    missing = REQUIRED_EFFECT_COLUMNS.difference(records.columns)
    if missing:
        raise ValueError(
            f"Verificação de efeito v2.12 sem colunas: {sorted(missing)}"
        )

    required_deploy = {
        "deployment_record_id",
        "implementation_package_id",
        "deployed_commit_sha",
        "deployment_state",
        "deployment_is_not_effect_verification",
        "automatic_deploy_enabled",
        "automatic_rollback_enabled",
    }
    missing_deploy = required_deploy.difference(deployments.columns)
    if missing_deploy:
        raise ValueError(
            f"Deploy v2.12 sem colunas: {sorted(missing_deploy)}"
        )

    deploy = deployments.copy()
    if deploy["deployment_record_id"].duplicated().any():
        raise ValueError("deployment_record_id duplicado.")
    lookup = deploy.set_index("deployment_record_id")
    allowed_effect_states = set(config["effect_states"])

    data = records.copy()
    for field in (
        "measured_at",
        "observation_window_start",
        "observation_window_end",
    ):
        parsed = pd.to_datetime(data[field], errors="coerce", utc=True)
        if parsed.isna().any():
            raise ValueError(f"{field} contém data/hora inválida.")
        data[field] = parsed.astype("string")

    rows = []
    for row in data.to_dict(orient="records"):
        deployment_id = str(row["deployment_record_id"]).strip()
        if deployment_id not in lookup.index:
            raise ValueError(
                f"deployment_record_id inexistente: {deployment_id}"
            )
        origin = lookup.loc[deployment_id]

        if not bool(origin["deployment_is_not_effect_verification"]):
            raise ValueError(
                "Deploy deve permanecer distinto da verificação de efeito."
            )
        if bool(origin["automatic_deploy_enabled"]):
            raise ValueError("Deploy automático não pode estar habilitado.")
        if bool(origin["automatic_rollback_enabled"]):
            raise ValueError("Rollback automático não pode estar habilitado.")

        state = str(row["effect_state"]).strip()
        if state not in allowed_effect_states:
            raise ValueError(f"effect_state inválido: {state}")

        start = pd.to_datetime(row["observation_window_start"], utc=True)
        end = pd.to_datetime(row["observation_window_end"], utc=True)
        measured = pd.to_datetime(row["measured_at"], utc=True)
        if end < start:
            raise ValueError("observation_window_end deve ser >= start.")
        if measured < end:
            raise ValueError(
                "measured_at deve ser igual ou posterior ao fim da janela observada."
            )

        for field in (
            "reviewer_role",
            "expected_behavior_summary",
            "observed_behavior_summary",
            "evidence_refs",
            "effect_review_notes",
        ):
            if _blank(row.get(field)):
                raise ValueError(f"{field} não pode ser vazio.")

        normalized = dict(row)
        normalized["implementation_package_id"] = str(
            origin["implementation_package_id"]
        )
        normalized["deployed_commit_sha"] = str(
            origin["deployed_commit_sha"]
        )
        normalized["effect_verification_record_id"] = _record_id(
            "effect_",
            deployment_id,
            normalized["measured_at"],
            state,
        )
        normalized["effect_verification_is_not_causal_inference"] = True
        normalized["automatic_rule_change_enabled"] = False
        normalized["automatic_rollback_enabled"] = False
        normalized["patient_level_decision_enabled"] = False
        normalized["human_effect_review_required"] = True
        normalized["personal_identifier_storage"] = False
        normalized["effect_verification_status"] = "human_post_deploy_effect_review"
        rows.append(normalized)

    out = pd.DataFrame(rows)
    if out["effect_verification_record_id"].duplicated().any():
        raise ValueError("effect_verification_record_id duplicado.")
    return out.sort_values(
        ["measured_at", "deployment_record_id"]
    ).reset_index(drop=True)
