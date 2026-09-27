# -*- coding: utf-8 -*-
from __future__ import annotations

import hashlib
import json
import re
from pathlib import Path

import pandas as pd


REQUIRED_DECISION_COLUMNS = {
    "postmortem_record_id",
    "evaluated_at",
    "reviewer_role",
    "action_coverage_review_status",
    "evidence_review_status",
    "rule_handoff_review_status",
    "closure_decision",
    "decision_rationale",
    "closure_evidence_refs",
}

REQUIRED_POSTMORTEM_COLUMNS = {
    "postmortem_record_id",
    "implementation_package_id",
    "conducted_at",
    "postmortem_status",
    "learning_action_type",
    "reenter_rule_review",
    "postmortem_is_not_causal_proof",
    "learning_is_not_rule_change",
    "automatic_rule_change_enabled",
    "automatic_issue_creation_enabled",
}

REQUIRED_ACTION_COLUMNS = {
    "learning_action_record_id",
    "postmortem_record_id",
    "learning_action_type",
    "follow_up_state",
    "as_of",
    "governance_handoff_ref",
    "tracking_is_not_execution",
    "completion_is_not_effectiveness_proof",
    "overdue_is_not_risk",
    "automatic_execution_enabled",
    "automatic_issue_creation_enabled",
    "automatic_rule_change_enabled",
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
}

TZ_RE = re.compile(r"(?:Z|[+-]\d{2}:\d{2})$", re.I)


def load_learning_cycle_closure_config(path: Path) -> dict:
    cfg = json.loads(path.read_text(encoding="utf-8"))
    principles = cfg.get("principles") or {}

    for key in (
        "postmortem_closed_is_not_learning_cycle_closed",
        "closure_is_not_epidemiological_effect",
        "closure_does_not_change_source_records",
        "human_closure_required",
    ):
        if principles.get(key) is not True:
            raise ValueError(f"{key} deve ser true.")

    for key in (
        "automatic_closure",
        "automatic_issue_creation",
        "automatic_rule_change",
        "automatic_deploy",
        "automatic_rollback",
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


def _timestamp(value: object, field: str) -> pd.Timestamp:
    if _blank(value):
        raise ValueError(f"{field} não pode ser vazio.")
    text = str(value).strip()
    if not TZ_RE.search(text):
        raise ValueError(f"{field} exige timezone explícito (Z ou ±HH:MM).")
    parsed = pd.to_datetime(text, errors="coerce", utc=True)
    if pd.isna(parsed):
        raise ValueError(f"{field} inválido.")
    return parsed


def _role_value(value: object, field: str) -> str:
    if _blank(value):
        raise ValueError(f"{field} não pode ser vazio.")
    text = str(value).strip()
    if not ROLE_RE.fullmatch(text):
        raise ValueError(
            f"{field} deve ser slug técnico de papel, sem nome pessoal ou espaços."
        )
    return text


def _reject_pii_text(value: object, field: str) -> str:
    text = "" if _blank(value) else str(value).strip()
    for label, pattern in PII_PATTERNS:
        if pattern.search(text):
            raise ValueError(
                f"{field} contém possível identificador pessoal ({label})."
            )
    return text


def _closure_record_id(postmortem_record_id: str, evaluated_at: str) -> str:
    basis = f"{postmortem_record_id}|{evaluated_at}"
    return "learning_closure_" + hashlib.sha256(
        basis.encode("utf-8")
    ).hexdigest()[:20]


def _validate_sources(
    postmortems: pd.DataFrame,
    actions: pd.DataFrame,
    config: dict,
) -> tuple[dict[str, dict], dict[str, pd.DataFrame]]:
    missing = REQUIRED_POSTMORTEM_COLUMNS.difference(postmortems.columns)
    if missing:
        raise ValueError(
            f"Post-mortem v2.14 sem colunas: {sorted(missing)}"
        )
    missing = REQUIRED_ACTION_COLUMNS.difference(actions.columns)
    if missing:
        raise ValueError(
            f"Follow-up v2.17 sem colunas: {sorted(missing)}"
        )

    eligible_statuses = set(config["eligible_postmortem_statuses"])
    postmortem_catalog: dict[str, dict] = {}

    for row in postmortems.to_dict(orient="records"):
        pid = str(row["postmortem_record_id"]).strip()
        status = str(row["postmortem_status"]).strip()
        if status not in eligible_statuses:
            continue
        if not _bool_value(row["postmortem_is_not_causal_proof"]):
            raise ValueError("Post-mortem deve permanecer não causal.")
        if not _bool_value(row["learning_is_not_rule_change"]):
            raise ValueError("Aprendizado deve permanecer distinto de mudança.")
        if _bool_value(row["automatic_rule_change_enabled"]):
            raise ValueError("Post-mortem não pode habilitar mudança automática de regra.")
        if _bool_value(row["automatic_issue_creation_enabled"]):
            raise ValueError("Post-mortem não pode habilitar criação automática de issue.")

        postmortem_catalog[pid] = {
            "implementation_package_id": str(
                row["implementation_package_id"]
            ).strip(),
            "conducted_at": _timestamp(
                row["conducted_at"], "conducted_at"
            ),
            "postmortem_status": status,
            "learning_action_type": str(
                row["learning_action_type"]
            ).strip(),
            "reenter_rule_review": _bool_value(
                row["reenter_rule_review"]
            ),
        }

    for row in actions.to_dict(orient="records"):
        if not _bool_value(row["tracking_is_not_execution"]):
            raise ValueError("Follow-up v2.17 deve permanecer distinto de execução.")
        if not _bool_value(row["completion_is_not_effectiveness_proof"]):
            raise ValueError("Conclusão v2.17 não pode equivaler a efetividade.")
        if not _bool_value(row["overdue_is_not_risk"]):
            raise ValueError("Overdue v2.17 deve permanecer distinto de risco.")
        if _bool_value(row["automatic_execution_enabled"]):
            raise ValueError("Follow-up v2.17 não pode habilitar execução automática.")
        if _bool_value(row["automatic_issue_creation_enabled"]):
            raise ValueError("Follow-up v2.17 não pode habilitar criação automática de issue.")
        if _bool_value(row["automatic_rule_change_enabled"]):
            raise ValueError("Follow-up v2.17 não pode habilitar mudança automática de regra.")

    grouped = {
        str(pid): frame.copy()
        for pid, frame in actions.groupby("postmortem_record_id", sort=False)
    }
    return postmortem_catalog, grouped


def validate_learning_cycle_closure(
    records: pd.DataFrame,
    postmortems: pd.DataFrame,
    actions: pd.DataFrame,
    config: dict,
) -> pd.DataFrame:
    missing = REQUIRED_DECISION_COLUMNS.difference(records.columns)
    if missing:
        raise ValueError(
            f"Gate v2.18 sem colunas: {sorted(missing)}"
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

    postmortem_catalog, grouped_actions = _validate_sources(
        postmortems, actions, config
    )

    review_statuses = set(config["review_statuses"])
    closure_decisions = set(config["closure_decisions"])
    terminal_states = set(config["terminal_action_states"])

    if records["postmortem_record_id"].astype(str).duplicated().any():
        raise ValueError(
            "Cada postmortem_record_id pode ter apenas uma decisão v2.18 por arquivo."
        )

    rows: list[dict] = []
    for row in records.to_dict(orient="records"):
        pid = str(row["postmortem_record_id"]).strip()
        if pid not in postmortem_catalog:
            raise ValueError(
                f"Post-mortem fechado e elegível não encontrado: {pid}"
            )
        source = postmortem_catalog[pid]

        evaluated_at = _timestamp(row["evaluated_at"], "evaluated_at")
        if evaluated_at < source["conducted_at"]:
            raise ValueError(
                "evaluated_at não pode ser anterior ao post-mortem."
            )
        reviewer_role = _role_value(
            row["reviewer_role"], "reviewer_role"
        )
        decision_rationale = _reject_pii_text(
            row["decision_rationale"], "decision_rationale"
        )
        if not decision_rationale:
            raise ValueError("decision_rationale não pode ser vazio.")

        coverage = str(row["action_coverage_review_status"]).strip()
        evidence = str(row["evidence_review_status"]).strip()
        handoff_review = str(row["rule_handoff_review_status"]).strip()
        decision = str(row["closure_decision"]).strip()
        closure_evidence = _reject_pii_text(
            row["closure_evidence_refs"], "closure_evidence_refs"
        )

        for label, value in (
            ("action_coverage_review_status", coverage),
            ("evidence_review_status", evidence),
            ("rule_handoff_review_status", handoff_review),
        ):
            if value not in review_statuses:
                raise ValueError(f"{label} inválido: {value}")
        if decision not in closure_decisions:
            raise ValueError(f"closure_decision inválido: {decision}")

        action_frame = grouped_actions.get(pid)
        action_count = 0 if action_frame is None else int(len(action_frame))
        states: list[str] = []
        snapshot_as_of: pd.Timestamp | None = None
        rule_handoff_present = False

        if action_frame is not None and not action_frame.empty:
            action_types = set(
                action_frame["learning_action_type"].astype(str)
            )
            if action_types != {source["learning_action_type"]}:
                raise ValueError(
                    f"{pid}: learning_action_type v2.17 diverge do post-mortem v2.14."
                )

            states = action_frame["follow_up_state"].astype(str).tolist()
            as_of_values = {
                _timestamp(value, "action.as_of")
                for value in action_frame["as_of"].tolist()
            }
            if len(as_of_values) != 1:
                raise ValueError(
                    f"{pid}: ações v2.17 devem compartilhar o mesmo as_of no snapshot."
                )
            snapshot_as_of = next(iter(as_of_values))
            if snapshot_as_of < evaluated_at:
                raise ValueError(
                    f"{pid}: snapshot v2.17 é anterior à avaliação de fechamento."
                )

            if source["learning_action_type"] == "rule_review":
                rule_handoff_present = bool(
                    action_frame.loc[
                        action_frame["follow_up_state"].astype(str).eq(
                            "verified_closed"
                        ),
                        "governance_handoff_ref",
                    ]
                    .fillna("")
                    .astype(str)
                    .str.strip()
                    .ne("")
                    .any()
                )

        all_terminal = bool(
            action_count > 0 and all(state in terminal_states for state in states)
        )
        blocking_states = sorted(
            {state for state in states if state not in terminal_states}
        )

        if source["learning_action_type"] == "rule_review":
            if handoff_review == "not_applicable":
                raise ValueError(
                    "rule_review exige rule_handoff_review_status passed/failed."
                )
        else:
            if handoff_review != "not_applicable":
                raise ValueError(
                    "Ação não rule_review exige rule_handoff_review_status=not_applicable."
                )

        if decision == "close_learning_cycle":
            if action_count == 0:
                raise ValueError(
                    "Fechamento exige ao menos uma ação v2.17."
                )
            if not all_terminal:
                raise ValueError(
                    "Fechamento bloqueado: existem ações v2.17 não terminais."
                )
            if coverage != "passed" or evidence != "passed":
                raise ValueError(
                    "Fechamento exige coverage/evidence review=passed."
                )
            if source["learning_action_type"] == "rule_review":
                if handoff_review != "passed" or not rule_handoff_present:
                    raise ValueError(
                        "rule_review só fecha com handoff revisado e presente."
                    )
            if not closure_evidence:
                raise ValueError(
                    "close_learning_cycle exige closure_evidence_refs."
                )

        final_state = {
            "close_learning_cycle": "learning_cycle_closed_human",
            "keep_open": "learning_cycle_open",
            "defer": "learning_cycle_closure_deferred",
        }[decision]

        rows.append({
            "learning_closure_record_id": _closure_record_id(
                pid, evaluated_at.isoformat()
            ),
            "postmortem_record_id": pid,
            "implementation_package_id": source[
                "implementation_package_id"
            ],
            "postmortem_status": source["postmortem_status"],
            "learning_action_type": source["learning_action_type"],
            "reenter_rule_review": source["reenter_rule_review"],
            "evaluated_at": evaluated_at.isoformat(),
            "reviewer_role": reviewer_role,
            "action_count": action_count,
            "terminal_action_count": sum(
                state in terminal_states for state in states
            ),
            "all_actions_terminal": all_terminal,
            "blocking_action_states": ";".join(blocking_states),
            "action_snapshot_as_of": (
                snapshot_as_of.isoformat()
                if snapshot_as_of is not None
                else ""
            ),
            "rule_handoff_present": rule_handoff_present,
            "action_coverage_review_status": coverage,
            "evidence_review_status": evidence,
            "rule_handoff_review_status": handoff_review,
            "closure_decision": decision,
            "decision_rationale": decision_rationale,
            "closure_evidence_refs": closure_evidence,
            "learning_cycle_state": final_state,
            "postmortem_closed_is_not_learning_cycle_closed": True,
            "closure_is_not_epidemiological_effect": True,
            "closure_does_not_change_source_records": True,
            "human_closure_required": True,
            "automatic_closure_enabled": False,
            "automatic_issue_creation_enabled": False,
            "automatic_rule_change_enabled": False,
            "automatic_deploy_enabled": False,
            "automatic_rollback_enabled": False,
            "personal_identifier_storage": False,
        })

    out = pd.DataFrame(rows)
    if not out.empty and out["learning_closure_record_id"].duplicated().any():
        raise ValueError("learning_closure_record_id duplicado.")
    return out.sort_values(
        ["evaluated_at", "postmortem_record_id"],
        kind="stable",
    ).reset_index(drop=True)
