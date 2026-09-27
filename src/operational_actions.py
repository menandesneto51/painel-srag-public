# -*- coding: utf-8 -*-
from __future__ import annotations

import json
from pathlib import Path

import pandas as pd


def _split_tags(value: object) -> set[str]:
    if value is None or pd.isna(value):
        return set()
    return {item.strip() for item in str(value).split("|") if item.strip()}


def _text(value: object) -> str:
    if value is None or pd.isna(value):
        return ""
    return str(value).strip()


def load_action_matrix(path: Path) -> dict:
    cfg = json.loads(path.read_text(encoding="utf-8"))
    principles = cfg.get("principles", {})
    if principles.get("automatic_execution") is not False:
        raise ValueError("Matriz operacional deve manter automatic_execution=false.")
    if principles.get("human_review_required") is not True:
        raise ValueError("Matriz operacional deve exigir revisão humana.")
    if principles.get("clinical_prescription") is not False:
        raise ValueError("Matriz operacional não pode habilitar prescrição clínica.")
    if principles.get("composite_score") is not False:
        raise ValueError("Matriz operacional não pode habilitar score composto.")

    actions = cfg.get("actions") or []
    ids = [str(a.get("action_id", "")) for a in actions]
    if not actions or len(ids) != len(set(ids)) or any(not x for x in ids):
        raise ValueError("action_id ausente ou duplicado na matriz.")
    return cfg


def _matches(action: dict, row: dict) -> bool:
    tags = _split_tags(row.get("review_tags"))

    trigger_tags = set(action.get("trigger_tags_any") or [])
    if trigger_tags and not tags.intersection(trigger_tags):
        return False

    signal_triggers = set(action.get("trigger_signal_status_any") or [])
    if signal_triggers and _text(row.get("signal_status")) not in signal_triggers:
        return False

    virology_triggers = set(action.get("trigger_virology_status_any") or [])
    if virology_triggers and _text(row.get("virology_status")) not in virology_triggers:
        return False

    confidence_required = set(action.get("requires_signal_confidence_any") or [])
    if confidence_required and _text(row.get("signal_confidence")) not in confidence_required:
        return False

    if action.get("requires_healthcare_pressure_available") is True:
        if not bool(row.get("healthcare_pressure_available", False)):
            return False

    pressure_status_required = set(
        action.get("requires_pressure_validation_status") or []
    )
    if pressure_status_required:
        if _text(row.get("validation_status")) not in pressure_status_required:
            return False

    return True


def build_operational_action_suggestions(
    territorial: pd.DataFrame,
    review_cards: pd.DataFrame,
    matrix: dict,
) -> pd.DataFrame:
    required_territorial = {
        "codigo_ibge",
        "municipio",
        "signal_status",
        "signal_confidence",
        "virology_status",
        "healthcare_pressure_available",
        "territorial_model_status",
    }
    missing = required_territorial.difference(territorial.columns)
    if missing:
        raise ValueError(
            f"Inteligência territorial sem colunas: {sorted(missing)}"
        )
    if "review_tags" not in review_cards.columns:
        raise ValueError("Cards de revisão sem review_tags.")

    t = territorial.copy()
    r = review_cards.copy()
    for optional_col in ("evidence_summary", "review_notes"):
        if optional_col not in r.columns:
            r[optional_col] = ""
    for frame in (t, r):
        frame["codigo_ibge"] = (
            frame["codigo_ibge"]
            .astype("string")
            .str.replace(r"\.0$", "", regex=True)
            .str.zfill(7)
        )

    if t["codigo_ibge"].duplicated().any():
        raise ValueError("Inteligência territorial possui município duplicado.")
    if r["codigo_ibge"].duplicated().any():
        raise ValueError("Cards possuem município duplicado.")

    merged = t.merge(
        r[[
            "codigo_ibge",
            "review_tags",
            "evidence_summary",
            "review_notes",
        ]],
        on="codigo_ibge",
        how="left",
        validate="one_to_one",
    )

    sources = matrix.get("sources") or {}
    suggestions: list[dict] = []
    for row in merged.to_dict(orient="records"):
        for action in matrix.get("actions") or []:
            if not _matches(action, row):
                continue

            refs = action.get("source_refs") or []
            source_titles = []
            source_urls = []
            for ref in refs:
                source = sources.get(ref) or {}
                if source.get("title"):
                    source_titles.append(source["title"])
                if source.get("url"):
                    source_urls.append(source["url"])

            suggestions.append({
                "codigo_ibge": _text(row.get("codigo_ibge")),
                "municipio": _text(row.get("municipio")),
                "action_id": action["action_id"],
                "domain": action["domain"],
                "title": action["title"],
                "suggested_review_owner": action["suggested_review_owner"],
                "suggested_timeframe": action["suggested_timeframe"],
                "action_text": action["action_text"],
                "trigger_review_tags": _text(row.get("review_tags")),
                "signal_status": _text(row.get("signal_status")),
                "signal_confidence": _text(row.get("signal_confidence")),
                "silence_status": _text(row.get("silence_status")),
                "virology_status": _text(row.get("virology_status")),
                "virology_dominant_agent": _text(
                    row.get("virology_dominant_agent")
                ),
                "pressure_status": _text(row.get("pressure_status")),
                "pressure_validation_status": _text(
                    row.get("validation_status")
                ),
                "evidence_summary": _text(row.get("evidence_summary")),
                "source_titles": " | ".join(source_titles),
                "source_urls": " | ".join(source_urls),
                "suggestion_status": "suggested_for_human_review",
                "human_review_required": True,
                "automatic_execution": False,
                "clinical_prescription": False,
                "composite_score_used": False,
            })

    columns = [
        "codigo_ibge",
        "municipio",
        "action_id",
        "domain",
        "title",
        "suggested_review_owner",
        "suggested_timeframe",
        "action_text",
        "trigger_review_tags",
        "signal_status",
        "signal_confidence",
        "silence_status",
        "virology_status",
        "virology_dominant_agent",
        "pressure_status",
        "pressure_validation_status",
        "evidence_summary",
        "source_titles",
        "source_urls",
        "suggestion_status",
        "human_review_required",
        "automatic_execution",
        "clinical_prescription",
        "composite_score_used",
    ]
    if not suggestions:
        return pd.DataFrame(columns=columns)

    out = pd.DataFrame(suggestions)
    if out.duplicated(["codigo_ibge", "action_id"]).any():
        raise ValueError("Ação operacional duplicada para o mesmo município.")

    return out[columns].sort_values(
        ["codigo_ibge", "domain", "action_id"]
    ).reset_index(drop=True)


def summarize_action_suggestions(actions: pd.DataFrame) -> pd.DataFrame:
    if actions.empty:
        return pd.DataFrame(
            columns=[
                "action_id",
                "domain",
                "title",
                "municipalities",
                "suggested_review_owner",
                "suggested_timeframe",
            ]
        )

    return (
        actions.groupby(
            [
                "action_id",
                "domain",
                "title",
                "suggested_review_owner",
                "suggested_timeframe",
            ],
            as_index=False,
        )
        .agg(municipalities=("codigo_ibge", "nunique"))
        .sort_values(["domain", "action_id"])
        .reset_index(drop=True)
    )
