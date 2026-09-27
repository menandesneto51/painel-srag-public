# -*- coding: utf-8 -*-
from __future__ import annotations

import json
from pathlib import Path

import pandas as pd


def parse_tags(value: object) -> list[str]:
    if value is None or pd.isna(value):
        return []
    tags = [tag.strip() for tag in str(value).split("|") if tag.strip()]
    return list(dict.fromkeys(tags))


def choose_review_queue(tags: list[str], rules: list[dict]) -> tuple[str, str]:
    tag_set = set(tags)
    for rule in rules:
        required_all = set(rule.get("requires_all_tags", []))
        required_any = set(rule.get("requires_any_tags", []))

        if required_all and not required_all.issubset(tag_set):
            continue
        if required_any and not required_any.intersection(tag_set):
            continue

        # Rule without conditions is the explicit fallback.
        if not required_all and not required_any:
            return str(rule["queue"]), str(rule.get("description", ""))

        return str(rule["queue"]), str(rule.get("description", ""))

    return "routine_monitoring", "Sem gatilho específico de revisão."


def build_operational_review_queue(
    review_cards: pd.DataFrame,
    config: dict,
) -> pd.DataFrame:
    required = {
        "codigo_ibge",
        "municipio",
        "review_tags",
        "evidence_summary",
        "human_review_required",
        "operational_recommendation_enabled",
        "composite_score_used",
    }
    missing = required.difference(review_cards.columns)
    if missing:
        raise ValueError(f"Cards sem colunas obrigatórias: {sorted(missing)}")

    actions_by_tag = dict(config["review_tag_actions"])
    rules = list(config["queue_rules"])

    rows = []
    for row in review_cards.itertuples(index=False):
        data = row._asdict()
        if not bool(data["human_review_required"]):
            raise ValueError("Todo card v2.2 deve exigir revisão humana.")
        if bool(data["operational_recommendation_enabled"]):
            raise ValueError("Cards com recomendação operacional automática não são aceitos.")
        if bool(data["composite_score_used"]):
            raise ValueError("Cards com score composto não são aceitos.")

        tags = parse_tags(data["review_tags"])
        queue, queue_description = choose_review_queue(tags, rules)

        actions: list[str] = []
        unknown_tags: list[str] = []
        for tag in tags:
            mapped = actions_by_tag.get(tag)
            if mapped is None:
                unknown_tags.append(tag)
                continue
            actions.extend(str(action) for action in mapped)

        actions = list(dict.fromkeys(actions))

        rows.append({
            "codigo_ibge": str(data["codigo_ibge"]),
            "municipio": str(data["municipio"]),
            "review_queue": queue,
            "queue_description": queue_description,
            "review_tags": "|".join(tags),
            "evidence_summary": str(data.get("evidence_summary", "")),
            "suggested_review_actions": " || ".join(actions),
            "unknown_review_tags": "|".join(unknown_tags),
            "human_review_required": True,
            "automatic_execution_enabled": False,
            "patient_level_decision_enabled": False,
            "composite_score_used": False,
            "queue_is_not_risk_rank": True,
            "operational_model_status": "experimental_review_workflow",
        })

    out = pd.DataFrame(rows)
    if out["codigo_ibge"].duplicated().any():
        raise ValueError("Fila operacional contém município duplicado.")
    return out.sort_values(["review_queue", "municipio"]).reset_index(drop=True)


def load_operational_config(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))
