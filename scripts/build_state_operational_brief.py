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

from src.operational_brief import (
    build_operational_review_queues,
    build_state_operational_brief,
)


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Gera filas de revisão e briefing estadual operacional SRAG v2.2."
    )
    parser.add_argument(
        "--actions",
        type=Path,
        default=(
            ROOT
            / "data_candidate"
            / "operational_actions"
            / "operational_action_suggestions_v2_2.csv"
        ),
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
        default=ROOT / "data_candidate" / "operational_actions",
    )
    args = parser.parse_args()

    if not args.actions.exists():
        raise FileNotFoundError(f"Ações sugeridas não encontradas: {args.actions}")

    actions = pd.read_csv(args.actions, dtype={"codigo_ibge": "string"})
    queues = build_operational_review_queues(actions)

    reference_week = None
    if args.territorial_metadata.exists():
        meta = json.loads(args.territorial_metadata.read_text(encoding="utf-8"))
        reference_week = meta.get("stable_week")

    brief = build_state_operational_brief(
        actions, queues, reference_week=reference_week
    )

    args.out_dir.mkdir(parents=True, exist_ok=True)
    queues_path = args.out_dir / "operational_review_queues_v2_2.csv"
    brief_path = args.out_dir / "state_operational_brief_v2_2.md"
    meta_path = args.out_dir / "state_operational_brief_v2_2.metadata.json"

    queues.to_csv(queues_path, index=False, encoding="utf-8")
    brief_path.write_text(brief, encoding="utf-8")

    metadata = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "reference_week": reference_week,
        "queues": int(len(queues)),
        "suggestions": int(len(actions)),
        "municipalities": (
            int(actions["codigo_ibge"].nunique()) if not actions.empty else 0
        ),
        "brief_status": "candidate_for_human_review",
        "automatic_execution": False,
        "composite_score": False,
    }
    meta_path.write_text(
        json.dumps(metadata, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    print(json.dumps(metadata, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
