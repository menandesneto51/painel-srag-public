# -*- coding: utf-8 -*-
from __future__ import annotations

import hashlib
import json
from pathlib import Path

import pandas as pd


REQUIRED_DECISION_COLUMNS = {
    "codigo_ibge",
    "municipio",
    "snapshot_id",
    "review_queue",
    "decision_scope",
    "reviewed_at",
    "reviewer_role",
    "decision_status",
    "rationale",
    "follow_up_required",
}

SAFE_OPTIONAL_DECISION_COLUMNS = [
    "action_id",
    "evidence_refs",
    "notes",
    "follow_up_due_at",
    "follow_up_owner_role",
]


def load_decision_config(path: Path) -> dict:
    cfg = json.loads(path.read_text(encoding="utf-8"))
    principles = cfg.get("principles") or {}
    if principles.get("automatic_execution") is not False:
        raise ValueError("v2.4 deve manter automatic_execution=false.")
    if principles.get("patient_level_decision") is not False:
        raise ValueError("v2.4 não pode habilitar decisão em nível de paciente.")
    if principles.get("clinical_prescription") is not False:
        raise ValueError("v2.4 não pode habilitar prescrição clínica.")
    if principles.get("human_decision_only") is not True:
        raise ValueError("v2.4 exige human_decision_only=true.")
    return cfg


def _ibge(value: object) -> str:
    text = "" if value is None else str(value).strip()
    if text.endswith(".0"):
        text = text[:-2]
    return text.zfill(7)


def _bool(value: object, field: str) -> bool:
    if isinstance(value, bool):
        return value
    text = "" if value is None else str(value).strip().lower()
    if text in {"true", "1", "yes", "sim"}:
        return True
    if text in {"false", "0", "no", "nao", "não"}:
        return False
    raise ValueError(f"{field} deve ser booleano explícito.")


def _blank(value: object) -> bool:
    return value is None or pd.isna(value) or str(value).strip() == ""


def _record_id(row: dict) -> str:
    basis = "|".join([
        str(row["snapshot_id"]),
        str(row["codigo_ibge"]),
        str(row["review_queue"]),
        str(row["decision_scope"]),
        str(row.get("action_id") or ""),
        str(row["reviewed_at"]),
        str(row["decision_status"]),
    ])
    return "dec_" + hashlib.sha256(basis.encode("utf-8")).hexdigest()[:20]


def validate_decision_audit(
    decisions: pd.DataFrame,
    municipal_queue: pd.DataFrame,
    action_suggestions: pd.DataFrame | None,
    config: dict,
) -> pd.DataFrame:
    missing = REQUIRED_DECISION_COLUMNS.difference(decisions.columns)
    if missing:
        raise ValueError(
            f"Decisões v2.4 sem colunas obrigatórias: {sorted(missing)}"
        )

    queue_required = {"codigo_ibge", "municipio", "review_queue"}
    missing_queue = queue_required.difference(municipal_queue.columns)
    if missing_queue:
        raise ValueError(
            f"Fila municipal sem colunas para auditoria: {sorted(missing_queue)}"
        )

    allowed_scopes = set(config["decision_scopes"])
    allowed_decisions = set(config["decision_statuses"])

    data = decisions.copy()
    for col in SAFE_OPTIONAL_DECISION_COLUMNS:
        if col not in data.columns:
            data[col] = ""

    data["codigo_ibge"] = data["codigo_ibge"].map(_ibge)
    if not data["codigo_ibge"].str.match(r"^51\d{5}$", na=False).all():
        raise ValueError("Há código IBGE inválido ou fora de Mato Grosso.")

    queue = municipal_queue.copy()
    queue["codigo_ibge"] = queue["codigo_ibge"].map(_ibge)
    if queue["codigo_ibge"].duplicated().any():
        raise ValueError("Fila municipal possui código IBGE duplicado.")

    queue_lookup = queue.set_index("codigo_ibge")

    actions = None
    if action_suggestions is not None and not action_suggestions.empty:
        action_required = {"codigo_ibge", "action_id"}
        missing_actions = action_required.difference(action_suggestions.columns)
        if missing_actions:
            raise ValueError(
                f"Sugestões de ação sem colunas: {sorted(missing_actions)}"
            )
        actions = action_suggestions.copy()
        actions["codigo_ibge"] = actions["codigo_ibge"].map(_ibge)
        if actions.duplicated(["codigo_ibge", "action_id"]).any():
            raise ValueError("Sugestões de ação possuem chave duplicada.")

    parsed_reviewed = pd.to_datetime(
        data["reviewed_at"], errors="coerce", utc=True
    )
    if parsed_reviewed.isna().any():
        raise ValueError("reviewed_at contém data/hora inválida.")
    data["reviewed_at"] = parsed_reviewed.astype("string")

    rows = []
    for record in data.to_dict(orient="records"):
        code = record["codigo_ibge"]
        if code not in queue_lookup.index:
            raise ValueError(
                f"Decisão referencia município ausente da fila: {code}"
            )

        expected_queue = str(queue_lookup.loc[code, "review_queue"])
        if str(record["review_queue"]).strip() != expected_queue:
            raise ValueError(
                f"{code}: review_queue da decisão não corresponde à fila de origem."
            )

        scope = str(record["decision_scope"]).strip()
        if scope not in allowed_scopes:
            raise ValueError(f"decision_scope inválido: {scope}")

        decision_status = str(record["decision_status"]).strip()
        if decision_status not in allowed_decisions:
            raise ValueError(f"decision_status inválido: {decision_status}")

        for field in ("snapshot_id", "reviewer_role", "rationale"):
            if _blank(record.get(field)):
                raise ValueError(f"{field} não pode ser vazio.")

        action_id = "" if _blank(record.get("action_id")) else str(
            record["action_id"]
        ).strip()
        if scope == "action":
            if not action_id:
                raise ValueError(
                    "decision_scope=action exige action_id."
                )
            if actions is None:
                raise ValueError(
                    "decision_scope=action exige tabela de sugestões de ação."
                )
            match = actions.loc[
                actions["codigo_ibge"].eq(code)
                & actions["action_id"].astype(str).eq(action_id)
            ]
            if len(match) != 1:
                raise ValueError(
                    f"{code}: action_id {action_id} não existe nas sugestões de origem."
                )
        elif action_id:
            raise ValueError(
                "decision_scope=queue não deve carregar action_id."
            )

        follow_required = _bool(
            record["follow_up_required"], "follow_up_required"
        )
        due_at = record.get("follow_up_due_at")
        owner = record.get("follow_up_owner_role")

        parsed_due = pd.NaT
        if follow_required:
            if _blank(due_at) or _blank(owner):
                raise ValueError(
                    "Follow-up requerido exige follow_up_due_at e follow_up_owner_role."
                )
            parsed_due = pd.to_datetime(due_at, errors="coerce", utc=True)
            if pd.isna(parsed_due):
                raise ValueError("follow_up_due_at inválido.")
            reviewed_ts = pd.to_datetime(record["reviewed_at"], utc=True)
            if parsed_due <= reviewed_ts:
                raise ValueError(
                    "follow_up_due_at deve ser posterior a reviewed_at."
                )
        else:
            if not _blank(due_at) or not _blank(owner):
                raise ValueError(
                    "Follow-up não requerido não deve definir prazo/responsável."
                )

        normalized = dict(record)
        normalized["action_id"] = action_id
        normalized["follow_up_required"] = follow_required
        normalized["follow_up_due_at"] = (
            str(parsed_due) if follow_required else ""
        )
        normalized["follow_up_owner_role"] = (
            str(owner).strip() if follow_required else ""
        )
        normalized["decision_record_id"] = _record_id(normalized)
        normalized["decision_recorded_by_human"] = True
        normalized["automatic_execution_enabled"] = False
        normalized["patient_level_decision_enabled"] = False
        normalized["clinical_prescription_enabled"] = False
        normalized["decision_is_not_proof_of_execution"] = True
        normalized["decision_audit_status"] = "human_decision_audit_record"
        rows.append(normalized)

    out = pd.DataFrame(rows)
    if out["decision_record_id"].duplicated().any():
        raise ValueError("Há decision_record_id duplicado.")

    ordered = [
        "decision_record_id",
        "codigo_ibge",
        "municipio",
        "snapshot_id",
        "review_queue",
        "decision_scope",
        "action_id",
        "reviewed_at",
        "reviewer_role",
        "decision_status",
        "rationale",
        "evidence_refs",
        "notes",
        "follow_up_required",
        "follow_up_due_at",
        "follow_up_owner_role",
        "decision_recorded_by_human",
        "automatic_execution_enabled",
        "patient_level_decision_enabled",
        "clinical_prescription_enabled",
        "decision_is_not_proof_of_execution",
        "decision_audit_status",
    ]
    return out[ordered].sort_values(
        ["reviewed_at", "codigo_ibge", "decision_record_id"]
    ).reset_index(drop=True)
