# -*- coding: utf-8 -*-
from __future__ import annotations

import hashlib
import json
import re
from pathlib import Path

import pandas as pd


REQUIRED_RELEASE_COLUMNS = {
    "post_merge_record_id",
    "evaluated_at",
    "reviewer_role",
    "target_environment",
    "release_commit_sha",
    "release_version",
    "release_notes_ref",
    "deployment_plan_ref",
    "monitoring_plan_ref",
    "rollback_plan_ref",
    "predeploy_ci_status",
    "predeploy_security_privacy_status",
    "monitoring_readiness_status",
    "rollback_plan_verification_status",
    "change_window_status",
    "final_release_decision",
    "release_rationale",
}


def load_release_gate_config(path: Path) -> dict:
    cfg = json.loads(path.read_text(encoding="utf-8"))
    p = cfg.get("principles") or {}

    for key in (
        "deploy_eligibility_is_not_deploy",
        "release_commit_must_match_verified_merge",
        "human_deploy_required",
        "human_review_required",
    ):
        if p.get(key) is not True:
            raise ValueError(f"{key} deve ser true.")

    for key in (
        "automatic_deploy",
        "automatic_rollback",
        "automatic_tagging",
    ):
        if p.get(key) is not False:
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


def _record_id(
    post_merge_record_id: str,
    target_environment: str,
    release_commit_sha: str,
    evaluated_at: str,
) -> str:
    basis = (
        f"{post_merge_record_id}|{target_environment}|"
        f"{release_commit_sha}|{evaluated_at}"
    )
    return "releasegate_" + hashlib.sha256(
        basis.encode("utf-8")
    ).hexdigest()[:20]


def _require_passed(
    row: dict,
    fields: tuple[str, ...],
    post_merge_record_id: str,
) -> None:
    failed = [
        field for field in fields
        if str(row.get(field, "")).strip() != "passed"
    ]
    if failed:
        raise ValueError(
            f"{post_merge_record_id}: elegibilidade para deploy bloqueada; "
            f"gates não aprovados: {failed}"
        )


def validate_release_deploy_gate(
    records: pd.DataFrame,
    post_merge: pd.DataFrame,
    config: dict,
) -> pd.DataFrame:
    missing = REQUIRED_RELEASE_COLUMNS.difference(records.columns)
    if missing:
        raise ValueError(
            f"Gate v2.12 sem colunas obrigatórias: {sorted(missing)}"
        )

    post_required = {
        "post_merge_record_id",
        "merge_decision_record_id",
        "merge_gate_record_id",
        "implementation_package_id",
        "merged_commit_sha",
        "post_merge_ci_status",
        "smoke_test_status",
        "epidemiology_sanity_status",
        "security_privacy_check_status",
        "rollback_readiness_status",
        "post_merge_state",
        "post_merge_record_requires_actual_merge_evidence",
        "post_merge_record_is_not_deploy",
        "automatic_deploy_enabled",
        "automatic_rollback_enabled",
        "human_post_merge_verification_required",
    }
    missing_post = post_required.difference(post_merge.columns)
    if missing_post:
        raise ValueError(
            f"Pós-merge v2.11 sem colunas: {sorted(missing_post)}"
        )

    source = post_merge.copy()
    if source["post_merge_record_id"].duplicated().any():
        raise ValueError("post_merge_record_id duplicado.")
    source_lookup = source.set_index("post_merge_record_id")

    allowed_state = str(config["allowed_post_merge_state"])
    allowed_rollback = str(config["allowed_rollback_readiness"])
    environments = set(config["target_environments"])
    review_statuses = set(config["review_statuses"])
    final_decisions = set(config["final_release_decisions"])

    data = records.copy()
    parsed = pd.to_datetime(data["evaluated_at"], errors="coerce", utc=True)
    if parsed.isna().any():
        raise ValueError("evaluated_at contém data/hora inválida.")
    data["evaluated_at"] = parsed.astype("string")

    rows = []
    for row in data.to_dict(orient="records"):
        post_id = str(row["post_merge_record_id"]).strip()
        if post_id not in source_lookup.index:
            raise ValueError(
                f"post_merge_record_id inexistente: {post_id}"
            )
        post = source_lookup.loc[post_id]

        if str(post["post_merge_state"]).strip() != allowed_state:
            raise ValueError(
                f"{post_id}: estado pós-merge não é {allowed_state}."
            )
        if str(post["rollback_readiness_status"]).strip() != allowed_rollback:
            raise ValueError(
                f"{post_id}: rollback readiness não é {allowed_rollback}."
            )
        if not bool(
            post["post_merge_record_requires_actual_merge_evidence"]
        ):
            raise ValueError(
                f"{post_id}: registro pós-merge sem exigência de evidência real."
            )
        if not bool(post["post_merge_record_is_not_deploy"]):
            raise ValueError(
                f"{post_id}: pós-merge deve permanecer distinto de deploy."
            )
        if bool(post["automatic_deploy_enabled"]):
            raise ValueError(
                f"{post_id}: deploy automático não pode estar habilitado."
            )
        if bool(post["automatic_rollback_enabled"]):
            raise ValueError(
                f"{post_id}: rollback automático não pode estar habilitado."
            )
        if not bool(post["human_post_merge_verification_required"]):
            raise ValueError(
                f"{post_id}: verificação humana pós-merge é obrigatória."
            )

        inherited_checks = (
            "post_merge_ci_status",
            "smoke_test_status",
            "epidemiology_sanity_status",
            "security_privacy_check_status",
        )
        inherited_failed = [
            field for field in inherited_checks
            if str(post[field]).strip() != "passed"
        ]
        if inherited_failed:
            raise ValueError(
                f"{post_id}: pós-merge não está saudável; "
                f"verificações falharam: {inherited_failed}"
            )

        environment = str(row["target_environment"]).strip().lower()
        if environment not in environments:
            raise ValueError(
                f"target_environment inválido: {environment}"
            )

        release_sha = _sha(
            row["release_commit_sha"],
            "release_commit_sha",
        )
        verified_sha = _sha(
            post["merged_commit_sha"],
            "merged_commit_sha",
        )
        if release_sha != verified_sha:
            raise ValueError(
                f"{post_id}: release_commit_sha difere do merged_commit_sha verificado."
            )

        for field in (
            "reviewer_role",
            "release_version",
            "release_notes_ref",
            "deployment_plan_ref",
            "monitoring_plan_ref",
            "rollback_plan_ref",
            "release_rationale",
        ):
            if _blank(row.get(field)):
                raise ValueError(f"{field} não pode ser vazio.")

        for field in (
            "predeploy_ci_status",
            "predeploy_security_privacy_status",
            "monitoring_readiness_status",
            "rollback_plan_verification_status",
            "change_window_status",
        ):
            status = str(row[field]).strip()
            if status not in review_statuses:
                raise ValueError(f"{field} inválido: {status}")

        decision = str(row["final_release_decision"]).strip()
        if decision not in final_decisions:
            raise ValueError(
                f"final_release_decision inválida: {decision}"
            )

        if decision == "eligible_for_human_deploy":
            _require_passed(
                row,
                (
                    "predeploy_ci_status",
                    "predeploy_security_privacy_status",
                    "monitoring_readiness_status",
                    "rollback_plan_verification_status",
                    "change_window_status",
                ),
                post_id,
            )

        normalized = dict(row)
        normalized["target_environment"] = environment
        normalized["merge_decision_record_id"] = str(
            post["merge_decision_record_id"]
        )
        normalized["merge_gate_record_id"] = str(
            post["merge_gate_record_id"]
        )
        normalized["implementation_package_id"] = str(
            post["implementation_package_id"]
        )
        normalized["verified_merged_commit_sha"] = verified_sha
        normalized["release_commit_sha"] = release_sha
        normalized["release_gate_record_id"] = _record_id(
            post_id,
            environment,
            release_sha,
            normalized["evaluated_at"],
        )
        normalized["deploy_eligibility_is_not_deploy"] = True
        normalized["automatic_tagging_enabled"] = False
        normalized["automatic_deploy_enabled"] = False
        normalized["automatic_rollback_enabled"] = False
        normalized["human_deploy_required"] = True
        normalized["human_review_required"] = True
        normalized["release_gate_status"] = "human_deploy_eligibility_gate"
        rows.append(normalized)

    out = pd.DataFrame(rows)
    if out["release_gate_record_id"].duplicated().any():
        raise ValueError("release_gate_record_id duplicado.")

    ordered = [
        "release_gate_record_id",
        "post_merge_record_id",
        "merge_decision_record_id",
        "merge_gate_record_id",
        "implementation_package_id",
        "evaluated_at",
        "reviewer_role",
        "target_environment",
        "verified_merged_commit_sha",
        "release_commit_sha",
        "release_version",
        "release_notes_ref",
        "deployment_plan_ref",
        "monitoring_plan_ref",
        "rollback_plan_ref",
        "predeploy_ci_status",
        "predeploy_security_privacy_status",
        "monitoring_readiness_status",
        "rollback_plan_verification_status",
        "change_window_status",
        "final_release_decision",
        "release_rationale",
        "deploy_eligibility_is_not_deploy",
        "automatic_tagging_enabled",
        "automatic_deploy_enabled",
        "automatic_rollback_enabled",
        "human_deploy_required",
        "human_review_required",
        "release_gate_status",
    ]
    return out[ordered].sort_values(
        ["evaluated_at", "target_environment", "post_merge_record_id"]
    ).reset_index(drop=True)
