# -*- coding: utf-8 -*-
from __future__ import annotations

import hashlib
import json
from pathlib import Path

import pandas as pd


REQUIRED_EVALUATION_COLUMNS = {
    "proposal_id",
    "evaluated_at",
    "reviewer_role",
    "case_review_status",
    "epidemiology_review_status",
    "backtest_status",
    "statistical_review_status",
    "documentation_status",
    "impact_summary",
    "risk_summary",
    "final_decision",
    "decision_rationale",
}

OPTIONAL_EVALUATION_COLUMNS = [
    "case_review_refs",
    "epidemiology_review_refs",
    "backtest_refs",
    "statistical_review_refs",
    "documentation_refs",
    "implementation_notes",
]


def load_evaluation_config(path: Path) -> dict:
    cfg = json.loads(path.read_text(encoding="utf-8"))
    p = cfg.get("principles") or {}
    for key in {
        "automatic_rule_change",
        "automatic_threshold_change",
        "automatic_merge",
        "automatic_deploy",
        "personal_identifier_storage",
    }:
        if p.get(key) is not False:
            raise ValueError(f"{key} deve ser false.")
    if p.get("proposal_is_not_change") is not True:
        raise ValueError("proposal_is_not_change deve ser true.")
    if p.get("decision_is_not_implementation") is not True:
        raise ValueError("decision_is_not_implementation deve ser true.")
    if p.get("human_approval_required") is not True:
        raise ValueError("human_approval_required deve ser true.")
    return cfg


def _blank(value: object) -> bool:
    return value is None or pd.isna(value) or str(value).strip() == ""


def _evaluation_id(proposal_id: str, evaluated_at: str, final_decision: str) -> str:
    basis = f"{proposal_id}|{evaluated_at}|{final_decision}"
    return "eval_" + hashlib.sha256(basis.encode("utf-8")).hexdigest()[:20]


def _passed(value: object) -> bool:
    return str(value).strip() == "passed"


def validate_rule_change_evaluations(
    evaluations: pd.DataFrame,
    proposals: pd.DataFrame,
    config: dict,
) -> pd.DataFrame:
    missing = REQUIRED_EVALUATION_COLUMNS.difference(evaluations.columns)
    if missing:
        raise ValueError(f"Avaliações v2.8 sem colunas: {sorted(missing)}")

    proposal_required = {
        "proposal_id",
        "proposal_type",
        "proposal_status",
        "proposal_is_not_change",
        "human_approval_required",
    }
    missing_proposals = proposal_required.difference(proposals.columns)
    if missing_proposals:
        raise ValueError(f"Propostas v2.7 sem colunas: {sorted(missing_proposals)}")

    p = proposals.copy()
    if p["proposal_id"].duplicated().any():
        raise ValueError("proposal_id duplicado nas propostas v2.7.")
    if not p["proposal_is_not_change"].astype(bool).all():
        raise ValueError("Há proposta v2.7 sem proposal_is_not_change=true.")
    if not p["human_approval_required"].astype(bool).all():
        raise ValueError("Há proposta v2.7 sem aprovação humana obrigatória.")

    review_statuses = set(config["review_statuses"])
    final_decisions = set(config["final_decisions"])
    logic_types = set(config["logic_change_types"])
    documentation_types = set(config["documentation_only_types"])

    data = evaluations.copy()
    for col in OPTIONAL_EVALUATION_COLUMNS:
        if col not in data.columns:
            data[col] = ""

    parsed = pd.to_datetime(data["evaluated_at"], errors="coerce", utc=True)
    if parsed.isna().any():
        raise ValueError("evaluated_at contém data/hora inválida.")
    data["evaluated_at"] = parsed.astype("string")

    proposal_lookup = p.set_index("proposal_id")
    rows = []

    for row in data.to_dict(orient="records"):
        proposal_id = str(row["proposal_id"]).strip()
        if proposal_id not in proposal_lookup.index:
            raise ValueError(
                f"Avaliação referencia proposal_id inexistente: {proposal_id}"
            )

        proposal_type = str(proposal_lookup.loc[proposal_id, "proposal_type"])
        if proposal_type not in logic_types | documentation_types:
            raise ValueError(
                f"proposal_type não suportado na v2.8: {proposal_type}"
            )

        for field in (
            "case_review_status",
            "epidemiology_review_status",
            "backtest_status",
            "statistical_review_status",
            "documentation_status",
        ):
            status = str(row[field]).strip()
            if status not in review_statuses:
                raise ValueError(f"{field} inválido: {status}")

        final_decision = str(row["final_decision"]).strip()
        if final_decision not in final_decisions:
            raise ValueError(f"final_decision inválida: {final_decision}")

        for field in (
            "reviewer_role",
            "impact_summary",
            "risk_summary",
            "decision_rationale",
        ):
            if _blank(row.get(field)):
                raise ValueError(f"{field} não pode ser vazio.")

        if final_decision == "approve_for_implementation_branch":
            if proposal_type in logic_types:
                mandatory = {
                    "case_review_status": row["case_review_status"],
                    "epidemiology_review_status": row["epidemiology_review_status"],
                    "backtest_status": row["backtest_status"],
                    "statistical_review_status": row["statistical_review_status"],
                    "documentation_status": row["documentation_status"],
                }
                failed = [
                    key for key, value in mandatory.items()
                    if not _passed(value)
                ]
                if failed:
                    raise ValueError(
                        f"{proposal_id}: aprovação bloqueada; revisões não aprovadas: {failed}"
                    )
            else:
                mandatory = {
                    "case_review_status": row["case_review_status"],
                    "epidemiology_review_status": row["epidemiology_review_status"],
                    "documentation_status": row["documentation_status"],
                }
                failed = [
                    key for key, value in mandatory.items()
                    if not _passed(value)
                ]
                if failed:
                    raise ValueError(
                        f"{proposal_id}: aprovação documental bloqueada; revisões não aprovadas: {failed}"
                    )
                for field in ("backtest_status", "statistical_review_status"):
                    if str(row[field]).strip() not in {"passed", "not_applicable"}:
                        raise ValueError(
                            f"{proposal_id}: {field} deve ser passed ou not_applicable."
                        )

        normalized = dict(row)
        normalized["proposal_type"] = proposal_type
        normalized["source_proposal_status"] = str(
            proposal_lookup.loc[proposal_id, "proposal_status"]
        )
        normalized["evaluation_record_id"] = _evaluation_id(
            proposal_id,
            normalized["evaluated_at"],
            final_decision,
        )
        normalized["evaluation_recorded_by_human"] = True
        normalized["proposal_is_not_change"] = True
        normalized["decision_is_not_implementation"] = True
        normalized["automatic_rule_change_enabled"] = False
        normalized["automatic_threshold_change_enabled"] = False
        normalized["automatic_merge_enabled"] = False
        normalized["automatic_deploy_enabled"] = False
        normalized["human_approval_required"] = True
        normalized["personal_identifier_storage"] = False
        normalized["evaluation_status"] = "human_rule_change_evaluation"
        rows.append(normalized)

    out = pd.DataFrame(rows)
    if out["evaluation_record_id"].duplicated().any():
        raise ValueError("evaluation_record_id duplicado.")

    ordered = [
        "evaluation_record_id",
        "proposal_id",
        "proposal_type",
        "source_proposal_status",
        "evaluated_at",
        "reviewer_role",
        "case_review_status",
        "case_review_refs",
        "epidemiology_review_status",
        "epidemiology_review_refs",
        "backtest_status",
        "backtest_refs",
        "statistical_review_status",
        "statistical_review_refs",
        "documentation_status",
        "documentation_refs",
        "impact_summary",
        "risk_summary",
        "final_decision",
        "decision_rationale",
        "implementation_notes",
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
    ]
    return out[ordered].sort_values(
        ["evaluated_at", "proposal_id"]
    ).reset_index(drop=True)
