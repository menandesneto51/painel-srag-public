# -*- coding: utf-8 -*-
from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.operational_actions import (
    build_operational_action_suggestions,
    load_action_matrix,
    summarize_action_suggestions,
)


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Gera ações sugeridas para revisão humana — SRAG MT v2.2."
    )
    parser.add_argument(
        "--territorial",
        type=Path,
        default=(
            ROOT
            / "data_candidate"
            / "territorial_intelligence"
            / "territorial_intelligence_v2_1.csv"
        ),
    )
    parser.add_argument(
        "--review-cards",
        type=Path,
        default=(
            ROOT
            / "data_candidate"
            / "territorial_intelligence"
            / "territorial_review_cards_v2_1.csv"
        ),
    )
    parser.add_argument(
        "--matrix",
        type=Path,
        default=ROOT / "config" / "operational_action_matrix_v2_2.json",
    )
    parser.add_argument(
        "--out-dir",
        type=Path,
        default=ROOT / "data_candidate" / "operational_actions",
    )
    args = parser.parse_args()

    for path in (args.territorial, args.review_cards, args.matrix):
        if not path.exists():
            raise FileNotFoundError(f"Entrada obrigatória ausente: {path}")

    territorial = pd.read_csv(
        args.territorial, dtype={"codigo_ibge": "string"}
    )
    review_cards = pd.read_csv(
        args.review_cards, dtype={"codigo_ibge": "string"}
    )
    matrix = load_action_matrix(args.matrix)

    actions = build_operational_action_suggestions(
        territorial, review_cards, matrix
    )
    summary = summarize_action_suggestions(actions)

    args.out_dir.mkdir(parents=True, exist_ok=True)
    actions_path = args.out_dir / "operational_action_suggestions_v2_2.csv"
    summary_path = args.out_dir / "operational_action_summary_v2_2.csv"
    meta_path = args.out_dir / "operational_action_suggestions_v2_2.metadata.json"

    actions.to_csv(actions_path, index=False, encoding="utf-8")
    summary.to_csv(summary_path, index=False, encoding="utf-8")

    metadata = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "matrix_id": matrix["matrix_id"],
        "version": matrix["version"],
        "status": matrix["status"],
        "suggestions": int(len(actions)),
        "municipalities_with_suggestions": (
            int(actions["codigo_ibge"].nunique()) if not actions.empty else 0
        ),
        "automatic_execution": False,
        "clinical_prescription": False,
        "composite_score": False,
        "human_review_required": True,
        "public_promotion_allowed": False,
    }
    meta_path.write_text(
        json.dumps(metadata, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

    print(json.dumps(metadata, ensure_ascii=False, indent=2))
    print(f"actions={actions_path}")
    print(f"summary={summary_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
