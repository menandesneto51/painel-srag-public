# -*- coding: utf-8 -*-
from __future__ import annotations

import hashlib
import json
import re
from pathlib import Path, PurePosixPath

import pandas as pd


REQUIRED_GATE_COLUMNS = {
    "implementation_package_id",
    "evaluated_at",
    "reviewer_role",
    "implementation_branch",
    "source_commit_sha",
    "implementation_commit_sha",
    "changed_paths",
    "diff_review_status",
    "scope_review_status",
    "ci_status",
    "regression_tests_status",
    "backtest_status",
    "epidemiology_revalidation_status",
    "statistical_revalidation_status",
    "security_privacy_review_status",
    "acceptance_criteria_status",
    "rollback_verification_status",
    "final_gate_decision",
    "gate_rationale",
}


def load_merge_gate_config(path: Path) -> dict:
    cfg = json.loads(path.read_text(encoding="utf-8"))
    principles = cfg.get("principles") or {}

    for key in (
        "merge_eligibility_is_not_merge",
        "implementation_branch_required",
        "source_commit_must_match_package",
        "implementation_commit_must_differ",
        "changed_paths_must_be_authorized",
        "human_merge_required",
        "human_review_required",
    ):
        if principles.get(key) is not True:
            raise ValueError(f"{key} deve ser true.")

    for key in ("automatic_merge", "automatic_deploy", "automatic_commit"):
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


def _parse_paths(value: object, field: str) -> list[str]:
    if _blank(value):
        raise ValueError(f"{field} não pode ser vazio.")
    paths = [
        item.strip().replace("\\", "/")
        for item in str(value).split("|")
        if item.strip()
    ]
    if not paths:
        raise ValueError(f"{field} não pode ser vazio.")
    for item in paths:
        path = PurePosixPath(item)
        if path.is_absolute() or ".." in path.parts:
            raise ValueError(f"{field} contém caminho inválido: {item}")
    return list(dict.fromkeys(paths))


def _path_authorized(changed: str, authorized: list[str]) -> bool:
    for target in authorized:
        normalized = target.rstrip("/")
        if changed == normalized:
            return True
        if target.endswith("/") and changed.startswith(normalized + "/"):
            return True
    return False


def _gate_id(
    package_id: str,
    implementation_commit_sha: str,
    evaluated_at: str,
) -> str:
    basis = f"{package_id}|{implementation_commit_sha}|{evaluated_at}"
    return "mergegate_" + hashlib.sha256(
        basis.encode("utf-8")
    ).hexdigest()[:20]


def _require_passed(
    row: dict,
    fields: tuple[str, ...],
    package_id: str,
) -> None:
    failed = [
        field for field in fields
        if str(row.get(field, "")).strip() != "passed"
    ]
    if failed:
        raise ValueError(
            f"{package_id}: elegibilidade para merge bloqueada; "
            f"gates não aprovados: {failed}"
        )


def validate_merge_gate(
    gate_records: pd.DataFrame,
    packages: pd.DataFrame,
    config: dict,
) -> pd.DataFrame:
    missing = REQUIRED_GATE_COLUMNS.difference(gate_records.columns)
    if missing:
        raise ValueError(
            f"Registros v2.10 sem colunas obrigatórias: {sorted(missing)}"
        )

    package_required = {
        "implementation_package_id",
        "proposal_id",
        "evaluation_record_id",
        "proposal_type",
        "package_status",
        "source_branch",
        "source_commit_sha",
        "target_paths",
        "package_is_not_implementation",
        "manual_branch_required",
        "automatic_branch_creation_enabled",
        "automatic_code_edit_enabled",
        "automatic_commit_enabled",
        "automatic_merge_enabled",
        "automatic_deploy_enabled",
        "human_review_required",
    }
    missing_package = package_required.difference(packages.columns)
    if missing_package:
        raise ValueError(
            f"Pacotes v2.9 sem colunas: {sorted(missing_package)}"
        )

    pkg = packages.copy()
    if pkg["implementation_package_id"].duplicated().any():
        raise ValueError("implementation_package_id duplicado.")
    pkg_lookup = pkg.set_index("implementation_package_id")

    allowed_package_status = set(config["allowed_package_status"])
    review_statuses = set(config["review_statuses"])
    final_decisions = set(config["final_gate_decisions"])
    protected_branches = set(config.get("protected_branch_names") or [])
    logic_types = set(config.get("logic_change_types") or [])
    documentation_types = set(config.get("documentation_only_types") or [])

    data = gate_records.copy()
    parsed = pd.to_datetime(data["evaluated_at"], errors="coerce", utc=True)
    if parsed.isna().any():
        raise ValueError("evaluated_at contém data/hora inválida.")
    data["evaluated_at"] = parsed.astype("string")

    rows: list[dict] = []

    for row in data.to_dict(orient="records"):
        package_id = str(row["implementation_package_id"]).strip()
        if package_id not in pkg_lookup.index:
            raise ValueError(
                f"implementation_package_id inexistente: {package_id}"
            )

        package = pkg_lookup.loc[package_id]

        if str(package["package_status"]).strip() not in allowed_package_status:
            raise ValueError(
                f"{package_id}: package_status não é elegível para gate v2.10."
            )
        if not bool(package["package_is_not_implementation"]):
            raise ValueError(
                f"{package_id}: pacote deve permanecer distinto de implementação."
            )
        if not bool(package["manual_branch_required"]):
            raise ValueError(
                f"{package_id}: branch manual deve permanecer obrigatória."
            )
        if not bool(package["human_review_required"]):
            raise ValueError(
                f"{package_id}: revisão humana deve permanecer obrigatória."
            )

        for field in (
            "automatic_branch_creation_enabled",
            "automatic_code_edit_enabled",
            "automatic_commit_enabled",
            "automatic_merge_enabled",
            "automatic_deploy_enabled",
        ):
            if bool(package[field]):
                raise ValueError(
                    f"{package_id}: pacote v2.9 habilita automação proibida em {field}."
                )

        branch = str(row["implementation_branch"]).strip()
        if not branch:
            raise ValueError("implementation_branch não pode ser vazio.")
        if branch in protected_branches:
            raise ValueError(
                f"{package_id}: implementation_branch não pode ser branch protegida."
            )
        source_branch = str(package["source_branch"]).strip()
        if branch == source_branch:
            raise ValueError(
                f"{package_id}: implementation_branch deve ser distinta da source_branch."
            )

        source_sha = _sha(row["source_commit_sha"], "source_commit_sha")
        package_source_sha = _sha(
            package["source_commit_sha"],
            "package.source_commit_sha",
        )
        if source_sha != package_source_sha:
            raise ValueError(
                f"{package_id}: source_commit_sha não corresponde ao pacote v2.9."
            )

        implementation_sha = _sha(
            row["implementation_commit_sha"],
            "implementation_commit_sha",
        )
        if implementation_sha == source_sha:
            raise ValueError(
                f"{package_id}: implementation_commit_sha deve diferir do source_commit_sha."
            )

        changed_paths = _parse_paths(row["changed_paths"], "changed_paths")
        authorized_paths = _parse_paths(
            package["target_paths"],
            "package.target_paths",
        )
        unauthorized = [
            path for path in changed_paths
            if not _path_authorized(path, authorized_paths)
        ]
        if unauthorized:
            raise ValueError(
                f"{package_id}: diff contém arquivos fora do escopo autorizado: "
                f"{unauthorized}"
            )

        for field in (
            "diff_review_status",
            "scope_review_status",
            "ci_status",
            "regression_tests_status",
            "backtest_status",
            "epidemiology_revalidation_status",
            "statistical_revalidation_status",
            "security_privacy_review_status",
            "acceptance_criteria_status",
            "rollback_verification_status",
        ):
            status = str(row[field]).strip()
            if status not in review_statuses:
                raise ValueError(f"{field} inválido: {status}")

        final_decision = str(row["final_gate_decision"]).strip()
        if final_decision not in final_decisions:
            raise ValueError(
                f"final_gate_decision inválida: {final_decision}"
            )
        if _blank(row.get("reviewer_role")):
            raise ValueError("reviewer_role não pode ser vazio.")
        if _blank(row.get("gate_rationale")):
            raise ValueError("gate_rationale não pode ser vazio.")

        proposal_type = str(package["proposal_type"]).strip()

        if final_decision == "eligible_for_human_merge":
            common_required = (
                "diff_review_status",
                "scope_review_status",
                "ci_status",
                "regression_tests_status",
                "epidemiology_revalidation_status",
                "security_privacy_review_status",
                "acceptance_criteria_status",
                "rollback_verification_status",
            )
            _require_passed(row, common_required, package_id)

            if proposal_type in logic_types:
                _require_passed(
                    row,
                    (
                        "backtest_status",
                        "statistical_revalidation_status",
                    ),
                    package_id,
                )
            elif proposal_type in documentation_types:
                for field in (
                    "backtest_status",
                    "statistical_revalidation_status",
                ):
                    if str(row[field]).strip() not in {
                        "passed",
                        "not_applicable",
                    }:
                        raise ValueError(
                            f"{package_id}: {field} deve ser passed ou not_applicable."
                        )
            else:
                raise ValueError(
                    f"{package_id}: proposal_type não suportado no gate v2.10."
                )

        normalized = dict(row)
        normalized["proposal_id"] = str(package["proposal_id"])
        normalized["evaluation_record_id"] = str(
            package["evaluation_record_id"]
        )
        normalized["proposal_type"] = proposal_type
        normalized["source_branch"] = source_branch
        normalized["source_commit_sha"] = source_sha
        normalized["implementation_commit_sha"] = implementation_sha
        normalized["changed_paths"] = " | ".join(changed_paths)
        normalized["authorized_target_paths"] = " | ".join(
            authorized_paths
        )
        normalized["merge_gate_record_id"] = _gate_id(
            package_id,
            implementation_sha,
            normalized["evaluated_at"],
        )
        normalized["merge_eligibility_is_not_merge"] = True
        normalized["automatic_commit_enabled"] = False
        normalized["automatic_merge_enabled"] = False
        normalized["automatic_deploy_enabled"] = False
        normalized["human_merge_required"] = True
        normalized["human_review_required"] = True
        normalized["gate_status"] = "human_merge_eligibility_gate"
        rows.append(normalized)

    out = pd.DataFrame(rows)
    if out["merge_gate_record_id"].duplicated().any():
        raise ValueError("merge_gate_record_id duplicado.")

    ordered = [
        "merge_gate_record_id",
        "implementation_package_id",
        "proposal_id",
        "evaluation_record_id",
        "proposal_type",
        "evaluated_at",
        "reviewer_role",
        "source_branch",
        "implementation_branch",
        "source_commit_sha",
        "implementation_commit_sha",
        "changed_paths",
        "authorized_target_paths",
        "diff_review_status",
        "scope_review_status",
        "ci_status",
        "regression_tests_status",
        "backtest_status",
        "epidemiology_revalidation_status",
        "statistical_revalidation_status",
        "security_privacy_review_status",
        "acceptance_criteria_status",
        "rollback_verification_status",
        "final_gate_decision",
        "gate_rationale",
        "merge_eligibility_is_not_merge",
        "automatic_commit_enabled",
        "automatic_merge_enabled",
        "automatic_deploy_enabled",
        "human_merge_required",
        "human_review_required",
        "gate_status",
    ]
    return out[ordered].sort_values(
        ["evaluated_at", "implementation_package_id"]
    ).reset_index(drop=True)
