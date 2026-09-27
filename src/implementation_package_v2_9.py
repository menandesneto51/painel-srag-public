# -*- coding: utf-8 -*-
from __future__ import annotations

import hashlib
import json
from pathlib import Path, PurePosixPath

import pandas as pd


REQUIRED_PACKAGE_COLUMNS = {
    "proposal_id",
    "evaluation_record_id",
    "created_at",
    "planner_role",
    "implementation_summary",
    "target_paths",
    "required_tests",
    "acceptance_criteria",
    "rollback_plan",
    "evidence_refs",
    "package_status",
}


def load_implementation_package_config(path: Path) -> dict:
    cfg = json.loads(path.read_text(encoding="utf-8"))
    p = cfg.get("principles") or {}
    if p.get("package_is_not_implementation") is not True:
        raise ValueError("package_is_not_implementation deve ser true.")
    if p.get("manual_branch_required") is not True:
        raise ValueError("manual_branch_required deve ser true.")
    for key in (
        "automatic_branch_creation",
        "automatic_code_edit",
        "automatic_commit",
        "automatic_merge",
        "automatic_deploy",
    ):
        if p.get(key) is not False:
            raise ValueError(f"{key} deve ser false.")
    if p.get("human_review_required") is not True:
        raise ValueError("human_review_required deve ser true.")
    return cfg


def _blank(value: object) -> bool:
    return value is None or pd.isna(value) or str(value).strip() == ""


def _package_id(proposal_id: str, evaluation_record_id: str) -> str:
    basis = f"{proposal_id}|{evaluation_record_id}"
    return "implpkg_" + hashlib.sha256(basis.encode("utf-8")).hexdigest()[:18]


def _target_branch_suggestion(proposal_id: str) -> str:
    safe = "".join(
        char if char.isalnum() or char in {"-", "_"} else "-"
        for char in str(proposal_id)
    ).strip("-")
    return f"change/{safe}"


def _parse_target_paths(value: object) -> list[str]:
    if _blank(value):
        raise ValueError("target_paths não pode ser vazio.")
    paths = [item.strip() for item in str(value).split("|") if item.strip()]
    if not paths:
        raise ValueError("target_paths não pode ser vazio.")
    return list(dict.fromkeys(paths))


def _validate_repo_path(
    path_text: str,
    protected_prefixes: list[str],
    protected_exact: set[str],
) -> None:
    normalized = path_text.replace("\\", "/").strip()
    path = PurePosixPath(normalized)

    if path.is_absolute():
        raise ValueError(f"target_path absoluto não permitido: {path_text}")
    if ".." in path.parts:
        raise ValueError(f"target_path com traversal não permitido: {path_text}")
    if normalized in protected_exact:
        raise ValueError(f"target_path protegido: {path_text}")
    for prefix in protected_prefixes:
        if normalized.startswith(prefix):
            raise ValueError(f"target_path protegido por prefixo: {path_text}")


def validate_implementation_packages(
    packages: pd.DataFrame,
    evaluations: pd.DataFrame,
    proposals: pd.DataFrame,
    config: dict,
) -> pd.DataFrame:
    missing = REQUIRED_PACKAGE_COLUMNS.difference(packages.columns)
    if missing:
        raise ValueError(
            f"Pacotes v2.9 sem colunas obrigatórias: {sorted(missing)}"
        )

    eval_required = {
        "evaluation_record_id",
        "proposal_id",
        "final_decision",
        "decision_is_not_implementation",
        "automatic_rule_change_enabled",
        "automatic_threshold_change_enabled",
        "automatic_merge_enabled",
        "automatic_deploy_enabled",
    }
    missing_eval = eval_required.difference(evaluations.columns)
    if missing_eval:
        raise ValueError(
            f"Avaliações v2.8 sem colunas: {sorted(missing_eval)}"
        )

    proposal_required = {
        "proposal_id",
        "proposal_type",
        "rule_key",
        "proposal_is_not_change",
        "human_approval_required",
    }
    missing_prop = proposal_required.difference(proposals.columns)
    if missing_prop:
        raise ValueError(
            f"Propostas v2.7 sem colunas: {sorted(missing_prop)}"
        )

    evals = evaluations.copy()
    if evals["evaluation_record_id"].duplicated().any():
        raise ValueError("evaluation_record_id duplicado.")
    eval_lookup = evals.set_index("evaluation_record_id")

    props = proposals.copy()
    if props["proposal_id"].duplicated().any():
        raise ValueError("proposal_id duplicado.")
    prop_lookup = props.set_index("proposal_id")

    allowed_decision = str(config["allowed_source_decision"])
    allowed_status = set(config["package_statuses"])
    protected_prefixes = list(config.get("protected_path_prefixes") or [])
    protected_exact = set(config.get("protected_exact_paths") or [])

    data = packages.copy()
    parsed = pd.to_datetime(data["created_at"], errors="coerce", utc=True)
    if parsed.isna().any():
        raise ValueError("created_at contém data/hora inválida.")
    data["created_at"] = parsed.astype("string")

    rows = []
    for row in data.to_dict(orient="records"):
        proposal_id = str(row["proposal_id"]).strip()
        evaluation_id = str(row["evaluation_record_id"]).strip()

        if evaluation_id not in eval_lookup.index:
            raise ValueError(
                f"evaluation_record_id inexistente: {evaluation_id}"
            )
        eval_row = eval_lookup.loc[evaluation_id]

        if str(eval_row["proposal_id"]).strip() != proposal_id:
            raise ValueError(
                f"{evaluation_id}: proposal_id não corresponde à avaliação."
            )
        if str(eval_row["final_decision"]).strip() != allowed_decision:
            raise ValueError(
                f"{evaluation_id}: decisão v2.8 não autoriza pacote v2.9."
            )
        if not bool(eval_row["decision_is_not_implementation"]):
            raise ValueError(
                f"{evaluation_id}: decisão deve permanecer distinta de implementação."
            )
        for field in (
            "automatic_rule_change_enabled",
            "automatic_threshold_change_enabled",
            "automatic_merge_enabled",
            "automatic_deploy_enabled",
        ):
            if bool(eval_row[field]):
                raise ValueError(
                    f"{evaluation_id}: {field} não pode estar habilitado."
                )

        if proposal_id not in prop_lookup.index:
            raise ValueError(f"proposal_id inexistente: {proposal_id}")
        prop_row = prop_lookup.loc[proposal_id]
        if not bool(prop_row["proposal_is_not_change"]):
            raise ValueError(
                f"{proposal_id}: proposta não preserva proposal_is_not_change."
            )
        if not bool(prop_row["human_approval_required"]):
            raise ValueError(
                f"{proposal_id}: proposta sem aprovação humana obrigatória."
            )

        for field in (
            "planner_role",
            "implementation_summary",
            "required_tests",
            "acceptance_criteria",
            "rollback_plan",
        ):
            if _blank(row.get(field)):
                raise ValueError(f"{field} não pode ser vazio.")

        status = str(row["package_status"]).strip()
        if status not in allowed_status:
            raise ValueError(f"package_status inválido: {status}")

        target_paths = _parse_target_paths(row["target_paths"])
        for target in target_paths:
            _validate_repo_path(
                target,
                protected_prefixes=protected_prefixes,
                protected_exact=protected_exact,
            )

        normalized = dict(row)
        normalized["proposal_type"] = str(prop_row["proposal_type"])
        normalized["rule_key"] = str(prop_row["rule_key"])
        normalized["target_paths"] = " | ".join(target_paths)
        normalized["implementation_package_id"] = _package_id(
            proposal_id,
            evaluation_id,
        )
        normalized["target_branch_suggestion"] = _target_branch_suggestion(
            proposal_id
        )
        normalized["package_is_not_implementation"] = True
        normalized["manual_branch_required"] = True
        normalized["automatic_branch_creation_enabled"] = False
        normalized["automatic_code_edit_enabled"] = False
        normalized["automatic_commit_enabled"] = False
        normalized["automatic_merge_enabled"] = False
        normalized["automatic_deploy_enabled"] = False
        normalized["human_review_required"] = True
        normalized["implementation_status"] = (
            "approved_package_for_manual_branch_preparation"
        )
        rows.append(normalized)

    out = pd.DataFrame(rows)
    if out["implementation_package_id"].duplicated().any():
        raise ValueError("implementation_package_id duplicado.")

    ordered = [
        "implementation_package_id",
        "proposal_id",
        "evaluation_record_id",
        "proposal_type",
        "rule_key",
        "created_at",
        "planner_role",
        "implementation_summary",
        "target_paths",
        "required_tests",
        "acceptance_criteria",
        "rollback_plan",
        "evidence_refs",
        "package_status",
        "target_branch_suggestion",
        "package_is_not_implementation",
        "manual_branch_required",
        "automatic_branch_creation_enabled",
        "automatic_code_edit_enabled",
        "automatic_commit_enabled",
        "automatic_merge_enabled",
        "automatic_deploy_enabled",
        "human_review_required",
        "implementation_status",
    ]
    return out[ordered].sort_values(
        ["created_at", "proposal_id"]
    ).reset_index(drop=True)
