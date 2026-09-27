# -*- coding: utf-8 -*-
from __future__ import annotations

import hashlib
import json
import re
from pathlib import Path, PurePosixPath

import pandas as pd


REQUIRED_PACKAGE_COLUMNS = {
    "proposal_id",
    "evaluation_record_id",
    "created_at",
    "planner_role",
    "source_branch",
    "source_commit_sha",
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
    principles = cfg.get("principles") or {}

    required_true = {
        "package_is_not_implementation",
        "manual_branch_required",
        "source_commit_required",
        "source_evaluation_must_be_human",
        "v2_8_gates_inherited",
        "human_review_required",
    }
    for key in required_true:
        if principles.get(key) is not True:
            raise ValueError(f"{key} deve ser true.")

    for key in (
        "automatic_branch_creation",
        "automatic_code_edit",
        "automatic_commit",
        "automatic_merge",
        "automatic_deploy",
    ):
        if principles.get(key) is not False:
            raise ValueError(f"{key} deve ser false.")

    return cfg


def _blank(value: object) -> bool:
    return value is None or pd.isna(value) or str(value).strip() == ""


def _package_id(
    proposal_id: str,
    evaluation_record_id: str,
    source_commit_sha: str,
) -> str:
    basis = f"{proposal_id}|{evaluation_record_id}|{source_commit_sha}"
    return "implpkg_" + hashlib.sha256(
        basis.encode("utf-8")
    ).hexdigest()[:18]


def _target_branch_suggestion(proposal_id: str) -> str:
    safe = "".join(
        char if char.isalnum() or char in {"-", "_"} else "-"
        for char in str(proposal_id)
    ).strip("-")
    return f"change/{safe}"


def _parse_target_paths(value: object) -> list[str]:
    if _blank(value):
        raise ValueError("target_paths não pode ser vazio.")
    paths = [
        item.strip()
        for item in str(value).split("|")
        if item.strip()
    ]
    if not paths:
        raise ValueError("target_paths não pode ser vazio.")
    return list(dict.fromkeys(paths))


def _validate_repo_path(
    path_text: str,
    protected_prefixes: list[str],
    protected_exact: set[str],
) -> None:
    normalized = path_text.replace("\\", "/").strip()
    if not normalized:
        raise ValueError("target_path vazio não permitido.")
    if re.match(r"^[A-Za-z]:", normalized):
        raise ValueError(
            f"target_path com drive absoluto não permitido: {path_text}"
        )

    path = PurePosixPath(normalized)
    if path.is_absolute():
        raise ValueError(
            f"target_path absoluto não permitido: {path_text}"
        )
    if ".." in path.parts:
        raise ValueError(
            f"target_path com traversal não permitido: {path_text}"
        )
    if normalized in protected_exact:
        raise ValueError(f"target_path protegido: {path_text}")
    for prefix in protected_prefixes:
        if normalized.startswith(prefix):
            raise ValueError(
                f"target_path protegido por prefixo: {path_text}"
            )


def _require_passed(
    source: pd.Series,
    proposal_id: str,
    fields: tuple[str, ...],
) -> None:
    failed = [
        field
        for field in fields
        if str(source.get(field, "")).strip() != "passed"
    ]
    if failed:
        raise ValueError(
            f"{proposal_id}: avaliação v2.8 não preserva gates "
            f"obrigatórios aprovados: {failed}"
        )


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
        "proposal_type",
        "source_proposal_status",
        "final_decision",
        "case_review_status",
        "epidemiology_review_status",
        "shadow_review_status",
        "shadow_evidence_present",
        "shadow_candidate_rule_version",
        "shadow_review_is_not_activation",
        "backtest_status",
        "statistical_review_status",
        "documentation_status",
        "evaluation_recorded_by_human",
        "proposal_is_not_change",
        "decision_is_not_implementation",
        "automatic_rule_change_enabled",
        "automatic_threshold_change_enabled",
        "automatic_merge_enabled",
        "automatic_deploy_enabled",
        "human_approval_required",
        "personal_identifier_storage",
        "evaluation_status",
    }
    missing_eval = eval_required.difference(evaluations.columns)
    if missing_eval:
        raise ValueError(
            f"Avaliações v2.8 sem colunas: {sorted(missing_eval)}"
        )

    proposal_required = {
        "proposal_id",
        "proposal_type",
        "proposal_status",
        "rule_key",
        "proposal_is_not_change",
        "human_approval_required",
        "automatic_rule_change_enabled",
        "automatic_threshold_change_enabled",
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
    allowed_eval_status = set(
        config.get(
            "allowed_source_evaluation_status",
            ["human_rule_change_evaluation"],
        )
    )
    allowed_prop_status = set(
        config.get(
            "allowed_source_proposal_status",
            ["ready_for_human_decision"],
        )
    )
    logic_types = set(config.get("logic_change_types") or [])
    documentation_types = set(
        config.get("documentation_only_types") or []
    )
    allowed_package_status = set(config["package_statuses"])
    protected_prefixes = list(
        config.get("protected_path_prefixes") or []
    )
    protected_exact = set(
        config.get("protected_exact_paths") or []
    )

    data = packages.copy()
    parsed = pd.to_datetime(
        data["created_at"], errors="coerce", utc=True
    )
    if parsed.isna().any():
        raise ValueError("created_at contém data/hora inválida.")
    data["created_at"] = parsed.astype("string")

    rows: list[dict] = []
    for row in data.to_dict(orient="records"):
        proposal_id = str(row["proposal_id"]).strip()
        evaluation_id = str(row["evaluation_record_id"]).strip()
        source_branch = str(row["source_branch"]).strip()
        source_commit_sha = str(row["source_commit_sha"]).strip().lower()

        if not source_branch:
            raise ValueError("source_branch não pode ser vazio.")
        if not re.fullmatch(r"[0-9a-f]{40}", source_commit_sha):
            raise ValueError(
                "source_commit_sha deve ser SHA Git completo de 40 "
                "caracteres hexadecimais."
            )

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
        if str(eval_row["evaluation_status"]).strip() not in allowed_eval_status:
            raise ValueError(
                f"{evaluation_id}: evaluation_status não é elegível."
            )
        if not bool(eval_row["evaluation_recorded_by_human"]):
            raise ValueError(
                f"{evaluation_id}: avaliação precisa ser registrada por humano."
            )
        if bool(eval_row["personal_identifier_storage"]):
            raise ValueError(
                f"{evaluation_id}: avaliação não pode armazenar "
                "identificador pessoal."
            )
        if not bool(eval_row["proposal_is_not_change"]):
            raise ValueError(
                f"{evaluation_id}: avaliação não preserva "
                "proposal_is_not_change."
            )
        if not bool(eval_row["decision_is_not_implementation"]):
            raise ValueError(
                f"{evaluation_id}: decisão deve permanecer distinta "
                "de implementação."
            )
        if not bool(eval_row["human_approval_required"]):
            raise ValueError(
                f"{evaluation_id}: aprovação humana deve permanecer obrigatória."
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

        proposal_type = str(prop_row["proposal_type"]).strip()
        if proposal_type != str(eval_row["proposal_type"]).strip():
            raise ValueError(
                f"{proposal_id}: proposal_type diverge entre v2.7 e v2.8."
            )
        source_proposal_status = str(
            eval_row["source_proposal_status"]
        ).strip()
        if source_proposal_status not in allowed_prop_status:
            raise ValueError(
                f"{proposal_id}: status da proposta de origem não é elegível."
            )
        if str(prop_row["proposal_status"]).strip() not in allowed_prop_status:
            raise ValueError(
                f"{proposal_id}: registro v2.7 não está em estado "
                "ready_for_human_decision."
            )
        if not bool(prop_row["proposal_is_not_change"]):
            raise ValueError(
                f"{proposal_id}: proposta não preserva proposal_is_not_change."
            )
        if not bool(prop_row["human_approval_required"]):
            raise ValueError(
                f"{proposal_id}: proposta sem aprovação humana obrigatória."
            )
        if bool(prop_row["automatic_rule_change_enabled"]):
            raise ValueError(
                f"{proposal_id}: proposta habilita alteração automática."
            )
        if bool(prop_row["automatic_threshold_change_enabled"]):
            raise ValueError(
                f"{proposal_id}: proposta habilita alteração automática "
                "de threshold."
            )

        if proposal_type in logic_types:
            _require_passed(
                eval_row,
                proposal_id,
                (
                    "case_review_status",
                    "epidemiology_review_status",
                    "shadow_review_status",
                    "backtest_status",
                    "statistical_review_status",
                    "documentation_status",
                ),
            )
            if not bool(eval_row["shadow_evidence_present"]):
                raise ValueError(
                    f"{proposal_id}: pacote lógico exige evidência shadow."
                )
            if not bool(eval_row["shadow_review_is_not_activation"]):
                raise ValueError(
                    f"{proposal_id}: shadow review deve permanecer "
                    "distinto de ativação."
                )
            if _blank(eval_row["shadow_candidate_rule_version"]):
                raise ValueError(
                    f"{proposal_id}: versão candidata shadow ausente."
                )
        elif proposal_type in documentation_types:
            _require_passed(
                eval_row,
                proposal_id,
                (
                    "case_review_status",
                    "epidemiology_review_status",
                    "documentation_status",
                ),
            )
            for field in (
                "shadow_review_status",
                "backtest_status",
                "statistical_review_status",
            ):
                if str(eval_row[field]).strip() not in {
                    "passed",
                    "not_applicable",
                }:
                    raise ValueError(
                        f"{proposal_id}: {field} deve ser passed ou "
                        "not_applicable."
                    )
        else:
            raise ValueError(
                f"{proposal_id}: proposal_type não suportado no pacote v2.9."
            )

        for field in (
            "planner_role",
            "implementation_summary",
            "required_tests",
            "acceptance_criteria",
            "rollback_plan",
            "evidence_refs",
        ):
            if _blank(row.get(field)):
                raise ValueError(f"{field} não pode ser vazio.")

        status = str(row["package_status"]).strip()
        if status not in allowed_package_status:
            raise ValueError(f"package_status inválido: {status}")

        target_paths = _parse_target_paths(row["target_paths"])
        for target in target_paths:
            _validate_repo_path(
                target,
                protected_prefixes=protected_prefixes,
                protected_exact=protected_exact,
            )

        normalized = dict(row)
        normalized["proposal_type"] = proposal_type
        normalized["rule_key"] = str(prop_row["rule_key"])
        normalized["source_proposal_status"] = source_proposal_status
        normalized["source_evaluation_status"] = str(
            eval_row["evaluation_status"]
        )
        normalized["source_shadow_review_status"] = str(
            eval_row["shadow_review_status"]
        )
        normalized["source_shadow_evidence_present"] = bool(
            eval_row["shadow_evidence_present"]
        )
        normalized["source_shadow_candidate_rule_version"] = str(
            eval_row["shadow_candidate_rule_version"]
        )
        normalized["source_backtest_status"] = str(
            eval_row["backtest_status"]
        )
        normalized["target_paths"] = " | ".join(target_paths)
        normalized["source_commit_sha"] = source_commit_sha
        normalized["implementation_package_id"] = _package_id(
            proposal_id,
            evaluation_id,
            source_commit_sha,
        )
        normalized["target_branch_suggestion"] = _target_branch_suggestion(
            proposal_id
        )
        normalized["package_is_not_implementation"] = True
        normalized["manual_branch_required"] = True
        normalized["source_commit_required"] = True
        normalized["v2_8_gates_inherited"] = True
        normalized["automatic_branch_creation_enabled"] = False
        normalized["automatic_code_edit_enabled"] = False
        normalized["automatic_commit_enabled"] = False
        normalized["automatic_merge_enabled"] = False
        normalized["automatic_deploy_enabled"] = False
        normalized["human_review_required"] = True
        normalized["implementation_status"] = (
            "validated_package_ready_for_manual_branch_preparation"
            if status == "ready_for_manual_branch"
            else f"validated_package_{status}"
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
        "source_proposal_status",
        "source_evaluation_status",
        "source_shadow_review_status",
        "source_shadow_evidence_present",
        "source_shadow_candidate_rule_version",
        "source_backtest_status",
        "created_at",
        "planner_role",
        "source_branch",
        "source_commit_sha",
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
        "source_commit_required",
        "v2_8_gates_inherited",
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
