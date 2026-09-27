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
from src.operational_brief import (
    build_operational_review_queues,
    build_state_operational_brief,
)
from src.operational_review import (
    build_operational_review_queue,
    load_operational_config,
)
from src.state_review_report import (
    build_state_review_summary,
    render_state_review_markdown,
)


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Executa a camada operacional v2.2 sem ranking ou execução automática."
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
        "--cards",
        type=Path,
        default=(
            ROOT
            / "data_candidate"
            / "territorial_intelligence"
            / "territorial_review_cards_v2_1.csv"
        ),
    )
    parser.add_argument(
        "--review-config",
        type=Path,
        default=ROOT / "config" / "operational_review_v2_2.json",
    )
    parser.add_argument(
        "--action-matrix",
        type=Path,
        default=ROOT / "config" / "operational_action_matrix_v2_2.json",
    )
    parser.add_argument(
        "--territorial-metadata",
        type=Path,
        default=(
            ROOT
            / "data_candidate"
            / "territorial_intelligence"
            / "territorial_intelligence_v2_1.metadata.json"
        ),
    )
    parser.add_argument(
        "--out-dir",
        type=Path,
        default=ROOT / "data_candidate" / "operational_v2_2",
    )
    args = parser.parse_args()

    for path in (
        args.territorial,
        args.cards,
        args.review_config,
        args.action_matrix,
    ):
        if not path.exists():
            raise FileNotFoundError(f"Entrada v2.2 ausente: {path}")

    territorial = pd.read_csv(
        args.territorial, dtype={"codigo_ibge": "string"}
    )
    cards = pd.read_csv(
        args.cards, dtype={"codigo_ibge": "string"}
    )

    review_config = load_operational_config(args.review_config)
    review_queue = build_operational_review_queue(cards, review_config)
    if len(review_queue) != 142 or review_queue["codigo_ibge"].nunique() != 142:
        raise ValueError("Fila de revisão v2.2 deve conter exatamente 142 municípios.")

    action_matrix = load_action_matrix(args.action_matrix)
    actions = build_operational_action_suggestions(
        territorial, cards, action_matrix
    )
    action_summary = summarize_action_suggestions(actions)
    review_queues_by_domain = build_operational_review_queues(actions)

    reference_week = None
    if args.territorial_metadata.exists():
        metadata = json.loads(
            args.territorial_metadata.read_text(encoding="utf-8")
        )
        reference_week = metadata.get("stable_week")

    state_review_summary = build_state_review_summary(review_queue)
    state_review_report = render_state_review_markdown(review_queue)
    state_operational_brief = build_state_operational_brief(
        actions,
        review_queues_by_domain,
        reference_week=reference_week,
    )

    args.out_dir.mkdir(parents=True, exist_ok=True)
    review_queue.to_csv(
        args.out_dir / "municipal_review_queue_v2_2.csv",
        index=False,
        encoding="utf-8",
    )
    actions.to_csv(
        args.out_dir / "operational_action_suggestions_v2_2.csv",
        index=False,
        encoding="utf-8",
    )
    action_summary.to_csv(
        args.out_dir / "operational_action_summary_v2_2.csv",
        index=False,
        encoding="utf-8",
    )
    review_queues_by_domain.to_csv(
        args.out_dir / "domain_review_queues_v2_2.csv",
        index=False,
        encoding="utf-8",
    )
    (args.out_dir / "state_review_report_v2_2.md").write_text(
        state_review_report, encoding="utf-8"
    )
    (args.out_dir / "state_operational_brief_v2_2.md").write_text(
        state_operational_brief, encoding="utf-8"
    )
    (args.out_dir / "state_review_summary_v2_2.json").write_text(
        json.dumps(state_review_summary, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

    run_meta = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "version": "2.2.0-experimental",
        "reference_week": reference_week,
        "municipality_queue_rows": int(len(review_queue)),
        "municipality_queue_count": int(
            review_queue["codigo_ibge"].nunique()
        ),
        "action_suggestions": int(len(actions)),
        "municipalities_with_action_suggestions": (
            int(actions["codigo_ibge"].nunique())
            if not actions.empty else 0
        ),
        "domain_review_queues": int(len(review_queues_by_domain)),
        "automatic_execution": False,
        "patient_level_decision": False,
        "clinical_prescription": False,
        "composite_score": False,
        "queue_is_not_risk_rank": True,
        "human_review_required": True,
        "public_promotion_allowed": False,
    }
    (args.out_dir / "v2_2_manifest.json").write_text(
        json.dumps(run_meta, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

    print(json.dumps(run_meta, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
