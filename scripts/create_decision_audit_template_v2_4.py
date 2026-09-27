# -*- coding: utf-8 -*-
from __future__ import annotations

import argparse
import json
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Gera template contextualizado para decisões humanas v2.4."
    )
    parser.add_argument(
        "--queue",
        type=Path,
        default=ROOT / "data_candidate" / "operational_v2_2" / "municipal_review_queue_v2_2.csv",
    )
    parser.add_argument(
        "--actions",
        type=Path,
        default=ROOT / "data_candidate" / "operational_v2_2" / "operational_action_suggestions_v2_2.csv",
    )
    parser.add_argument(
        "--territorial-metadata",
        type=Path,
        default=ROOT / "data_candidate" / "territorial_intelligence" / "territorial_intelligence_v2_1.metadata.json",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=ROOT / "data_candidate" / "decision_audit_v2_4" / "human_decision_template_v2_4.csv",
    )
    args = parser.parse_args()

    if not args.queue.exists():
        raise FileNotFoundError(args.queue)

    queue = pd.read_csv(args.queue, dtype={"codigo_ibge": "string"})
    required = {"codigo_ibge", "municipio", "review_queue"}
    missing = required.difference(queue.columns)
    if missing:
        raise ValueError(f"Fila municipal sem colunas: {sorted(missing)}")

    snapshot_id = ""
    if args.territorial_metadata.exists():
        metadata = json.loads(args.territorial_metadata.read_text(encoding="utf-8"))
        snapshot_id = str(
            metadata.get("snapshot_id")
            or metadata.get("source_snapshot_id")
            or metadata.get("generated_at")
            or ""
        )

    actions_by_code: dict[str, list[str]] = {}
    if args.actions.exists():
        actions = pd.read_csv(args.actions, dtype={"codigo_ibge": "string"})
        if {"codigo_ibge", "action_id"}.issubset(actions.columns):
            for code, group in actions.groupby("codigo_ibge", sort=False):
                actions_by_code[str(code)] = sorted(
                    group["action_id"].astype(str).unique().tolist()
                )

    template = queue[["codigo_ibge", "municipio", "review_queue"]].copy()
    template["snapshot_id"] = snapshot_id
    template["available_action_ids"] = template["codigo_ibge"].map(
        lambda code: "|".join(actions_by_code.get(str(code), []))
    )
    template["decision_scope"] = "queue"
    template["action_id"] = ""
    template["reviewed_at"] = ""
    template["reviewer_role"] = ""
    template["decision_status"] = ""
    template["rationale"] = ""
    template["evidence_refs"] = ""
    template["notes"] = ""
    template["follow_up_required"] = False
    template["follow_up_due_at"] = ""
    template["follow_up_owner_role"] = ""

    args.output.parent.mkdir(parents=True, exist_ok=True)
    template.to_csv(args.output, index=False, encoding="utf-8")
    print(f"rows={len(template)}")
    print(f"output={args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
