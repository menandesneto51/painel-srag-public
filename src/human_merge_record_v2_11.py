# -*- coding: utf-8 -*-
from __future__ import annotations

import hashlib
import json
import re
from pathlib import Path

import pandas as pd


REQUIRED_MERGE_DECISION_COLUMNS = {
    "merge_gate_record_id",
    "decided_at",
    "reviewer_role",
    "merge_decision",
    "decision_rationale",
}

REQUIRED_POST_MERGE_COLUMNS = {
    "merge_decision_record_id",
    "recorded_at",
    "reviewer_role",
    "merged_commit_sha",
    "merge_evidence_ref",
    "post_merge_ci_status",
    "smoke_test_status",
    "epidemiology_sanity_status",
    "security_privacy_check_status",
    "rollback_readiness_status",
    "post_merge_state",
    "verification_notes",
}


def load_merge_record_config(path: Path) -> dict:
    cfg = json.loads(path.read_text(encoding="utf-8"))
    principles = cfg.get("principles") or {}

    for key in (
        "merge_decision_is_not_merge_execution",
        "post_merge_record_requires_actual_merge_evidence",
        "human_merge_required",
        "human_post_merge_verification_required",
    ):
        if principles.get(key) is not True:
            raise ValueError(f"{key} deve ser true.")

    for key in (
        "automatic_merge",
        "automatic_deploy",
        "automatic_rollback",
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


def _decision_id(
    merge_gate_record_id: str,
    decided_at: str,
    merge_decision: str,
) -> str:
    basis = f"{merge_gate_record_id}|{decided_at}|{merge_decision}"
    return "mergedec_" + hashlib.sha256(
        basis.encode("utf-8")
    ).hexdigest()[:20]


def _post_merge_id(
    merge_decision_record_id: str,
    merged_commit_sha: str,
    recorded_at: str,
) -> str:
    basis = f"{merge_decision_record_id}|{merged_commit_sha}|{recorded_at}"
    return "postmerge_" + hashlib.sha256(
        basis.encode("utf-8")
    ).hexdigest()[:20]


def validate_human_merge_decisions(
    decisions: pd.DataFrame,
    merge_gate_records: pd.DataFrame,
    config: dict,
) -> pd.DataFrame:
    missing = REQUIRED_MERGE_DECISION_COLUMNS.difference(decisions.columns)
    if missing:
        raise ValueError(
            f"Decisões de merge v2.11 sem colunas: {sorted(missing)}"
        )

    gate_required = {
        "merge_gate_record_id",
        "implementation_package_id",
        "proposal_id",
        "evaluation_record_id",
        "implementation_branch",
        "implementation_commit_sha",
        "final_gate_decision",
        "merge_eligibility_is_not_merge",
        "automatic_merge_enabled",
        "automatic_deploy_enabled",
        "human_merge_required",
    }
    missing_gate = gate_required.difference(merge_gate_records.columns)
    if missing_gate:
        raise ValueError(
            f"Gate v2.10 sem colunas: {sorted(missing_gate)}"
        )

    gate = merge_gate_records.copy()
    if gate["merge_gate_record_id"].duplicated().any():
        raise ValueError("merge_gate_record_id duplicado.")
    gate_lookup = gate.set_index("merge_gate_record_id")

    allowed_gate_decision = str(config["allowed_gate_decision"])
    merge_decisions = set(config["merge_decisions"])

    data = decisions.copy()
    parsed = pd.to_datetime(data["decided_at"], errors="coerce", utc=True)
    if parsed.isna().any():
        raise ValueError("decided_at contém data/hora inválida.")
    data["decided_at"] = parsed.astype("string")

    rows = []
    for row in data.to_dict(orient="records"):
        gate_id = str(row["merge_gate_record_id"]).strip()
        if gate_id not in gate_lookup.index:
            raise ValueError(
                f"merge_gate_record_id inexistente: {gate_id}"
            )
        source = gate_lookup.loc[gate_id]

        if str(source["final_gate_decision"]).strip() != allowed_gate_decision:
            raise ValueError(
                f"{gate_id}: gate v2.10 não está elegível para decisão de merge."
            )
        if not bool(source["merge_eligibility_is_not_merge"]):
            raise ValueError(
                f"{gate_id}: elegibilidade deve permanecer distinta de merge."
            )
        if bool(source["automatic_merge_enabled"]):
            raise ValueError(
                f"{gate_id}: merge automático não pode estar habilitado."
            )
        if bool(source["automatic_deploy_enabled"]):
            raise ValueError(
                f"{gate_id}: deploy automático não pode estar habilitado."
            )
        if not bool(source["human_merge_required"]):
            raise ValueError(
                f"{gate_id}: merge humano deve permanecer obrigatório."
            )

        merge_decision = str(row["merge_decision"]).strip()
        if merge_decision not in merge_decisions:
            raise ValueError(
                f"merge_decision inválida: {merge_decision}"
            )
        if _blank(row.get("reviewer_role")):
            raise ValueError("reviewer_role não pode ser vazio.")
        if _blank(row.get("decision_rationale")):
            raise ValueError("decision_rationale não pode ser vazio.")

        implementation_sha = _sha(
            source["implementation_commit_sha"],
            "implementation_commit_sha",
        )

        normalized = dict(row)
        normalized["implementation_package_id"] = str(
            source["implementation_package_id"]
        )
        normalized["proposal_id"] = str(source["proposal_id"])
        normalized["evaluation_record_id"] = str(
            source["evaluation_record_id"]
        )
        normalized["implementation_branch"] = str(
            source["implementation_branch"]
        )
        normalized["implementation_commit_sha"] = implementation_sha
        normalized["merge_decision_record_id"] = _decision_id(
            gate_id,
            normalized["decided_at"],
            merge_decision,
        )
        normalized["merge_decision_is_not_merge_execution"] = True
        normalized["automatic_merge_enabled"] = False
        normalized["automatic_deploy_enabled"] = False
        normalized["automatic_rollback_enabled"] = False
        normalized["human_merge_required"] = True
        normalized["personal_identifier_storage"] = False
        normalized["decision_status"] = "human_merge_decision_record"
        rows.append(normalized)

    out = pd.DataFrame(rows)
    if out["merge_decision_record_id"].duplicated().any():
        raise ValueError("merge_decision_record_id duplicado.")

    ordered = [
        "merge_decision_record_id",
        "merge_gate_record_id",
        "implementation_package_id",
        "proposal_id",
        "evaluation_record_id",
        "implementation_branch",
        "implementation_commit_sha",
        "decided_at",
        "reviewer_role",
        "merge_decision",
        "decision_rationale",
        "merge_decision_is_not_merge_execution",
        "automatic_merge_enabled",
        "automatic_deploy_enabled",
        "automatic_rollback_enabled",
        "human_merge_required",
        "personal_identifier_storage",
        "decision_status",
    ]
    return out[ordered].sort_values(
        ["decided_at", "merge_gate_record_id"]
    ).reset_index(drop=True)


def validate_post_merge_records(
    records: pd.DataFrame,
    merge_decisions: pd.DataFrame,
    config: dict,
) -> pd.DataFrame:
    missing = REQUIRED_POST_MERGE_COLUMNS.difference(records.columns)
    if missing:
        raise ValueError(
            f"Registros pós-merge v2.11 sem colunas: {sorted(missing)}"
        )

    decision_required = {
        "merge_decision_record_id",
        "merge_gate_record_id",
        "implementation_package_id",
        "implementation_branch",
        "implementation_commit_sha",
        "merge_decision",
        "merge_decision_is_not_merge_execution",
        "automatic_merge_enabled",
        "automatic_deploy_enabled",
    }
    missing_decision = decision_required.difference(merge_decisions.columns)
    if missing_decision:
        raise ValueError(
            f"Decisões v2.11 sem colunas: {sorted(missing_decision)}"
        )

    decisions = merge_decisions.copy()
    if decisions["merge_decision_record_id"].duplicated().any():
        raise ValueError("merge_decision_record_id duplicado.")
    decision_lookup = decisions.set_index("merge_decision_record_id")

    verification_statuses = set(config["verification_statuses"])
    rollback_statuses = set(config["rollback_readiness_statuses"])
    post_states = set(config["post_merge_states"])

    data = records.copy()
    parsed = pd.to_datetime(data["recorded_at"], errors="coerce", utc=True)
    if parsed.isna().any():
        raise ValueError("recorded_at contém data/hora inválida.")
    data["recorded_at"] = parsed.astype("string")

    rows = []
    for row in data.to_dict(orient="records"):
        decision_id = str(row["merge_decision_record_id"]).strip()
        if decision_id not in decision_lookup.index:
            raise ValueError(
                f"merge_decision_record_id inexistente: {decision_id}"
            )
        source = decision_lookup.loc[decision_id]

        if str(source["merge_decision"]).strip() != "approve_human_merge":
            raise ValueError(
                f"{decision_id}: somente decisão approve_human_merge "
                "pode originar registro pós-merge."
            )
        if not bool(source["merge_decision_is_not_merge_execution"]):
            raise ValueError(
                f"{decision_id}: decisão deve permanecer distinta de execução."
            )
        if bool(source["automatic_merge_enabled"]):
            raise ValueError(
                f"{decision_id}: merge automático não pode estar habilitado."
            )
        if bool(source["automatic_deploy_enabled"]):
            raise ValueError(
                f"{decision_id}: deploy automático não pode estar habilitado."
            )

        merged_sha = _sha(row["merged_commit_sha"], "merged_commit_sha")
        implementation_sha = _sha(
            source["implementation_commit_sha"],
            "implementation_commit_sha",
        )
        if merged_sha == implementation_sha:
            # Fast-forward merge pode resultar no mesmo commit; isso é permitido,
            # mas precisa ser evidência explícita registrada por humano.
            merge_mode = "fast_forward_or_equivalent"
        else:
            merge_mode = "merge_commit_or_rebased_result"

        for field in (
            "post_merge_ci_status",
            "smoke_test_status",
            "epidemiology_sanity_status",
            "security_privacy_check_status",
        ):
            status = str(row[field]).strip()
            if status not in verification_statuses:
                raise ValueError(f"{field} inválido: {status}")

        rollback_status = str(
            row["rollback_readiness_status"]
        ).strip()
        if rollback_status not in rollback_statuses:
            raise ValueError(
                f"rollback_readiness_status inválido: {rollback_status}"
            )

        post_state = str(row["post_merge_state"]).strip()
        if post_state not in post_states:
            raise ValueError(
                f"post_merge_state inválido: {post_state}"
            )
        if _blank(row.get("reviewer_role")):
            raise ValueError("reviewer_role não pode ser vazio.")
        if _blank(row.get("merge_evidence_ref")):
            raise ValueError("merge_evidence_ref não pode ser vazio.")
        if _blank(row.get("verification_notes")):
            raise ValueError("verification_notes não pode ser vazio.")

        if post_state == "verified_healthy":
            required_passed = (
                "post_merge_ci_status",
                "smoke_test_status",
                "epidemiology_sanity_status",
                "security_privacy_check_status",
            )
            failed = [
                field for field in required_passed
                if str(row[field]).strip() != "passed"
            ]
            if failed:
                raise ValueError(
                    f"{decision_id}: verified_healthy bloqueado; "
                    f"verificações não aprovadas: {failed}"
                )
            if rollback_status != "ready":
                raise ValueError(
                    f"{decision_id}: verified_healthy exige rollback readiness ready."
                )

        normalized = dict(row)
        normalized["merge_gate_record_id"] = str(
            source["merge_gate_record_id"]
        )
        normalized["implementation_package_id"] = str(
            source["implementation_package_id"]
        )
        normalized["implementation_branch"] = str(
            source["implementation_branch"]
        )
        normalized["implementation_commit_sha"] = implementation_sha
        normalized["merged_commit_sha"] = merged_sha
        normalized["merge_result_mode"] = merge_mode
        normalized["post_merge_record_id"] = _post_merge_id(
            decision_id,
            merged_sha,
            normalized["recorded_at"],
        )
        normalized["post_merge_record_requires_actual_merge_evidence"] = True
        normalized["post_merge_record_is_not_deploy"] = True
        normalized["automatic_merge_enabled"] = False
        normalized["automatic_deploy_enabled"] = False
        normalized["automatic_rollback_enabled"] = False
        normalized["human_post_merge_verification_required"] = True
        normalized["personal_identifier_storage"] = False
        normalized["post_merge_record_status"] = "human_post_merge_verification_record"
        rows.append(normalized)

    out = pd.DataFrame(rows)
    if out["post_merge_record_id"].duplicated().any():
        raise ValueError("post_merge_record_id duplicado.")

    ordered = [
        "post_merge_record_id",
        "merge_decision_record_id",
        "merge_gate_record_id",
        "implementation_package_id",
        "implementation_branch",
        "implementation_commit_sha",
        "merged_commit_sha",
        "merge_result_mode",
        "merge_evidence_ref",
        "recorded_at",
        "reviewer_role",
        "post_merge_ci_status",
        "smoke_test_status",
        "epidemiology_sanity_status",
        "security_privacy_check_status",
        "rollback_readiness_status",
        "post_merge_state",
        "verification_notes",
        "post_merge_record_requires_actual_merge_evidence",
        "post_merge_record_is_not_deploy",
        "automatic_merge_enabled",
        "automatic_deploy_enabled",
        "automatic_rollback_enabled",
        "human_post_merge_verification_required",
        "personal_identifier_storage",
        "post_merge_record_status",
    ]
    return out[ordered].sort_values(
        ["recorded_at", "merge_decision_record_id"]
    ).reset_index(drop=True)
