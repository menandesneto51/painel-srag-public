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

from src.territorial_review_cards import build_review_cards


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Gera cards explicáveis de revisão municipal da inteligência territorial v2.1."
    )
    parser.add_argument(
        "--input",
        type=Path,
        default=(
            ROOT
            / "data_candidate"
            / "territorial_intelligence"
            / "territorial_intelligence_v2_1.csv"
        ),
    )
    parser.add_argument(
        "--out-dir",
        type=Path,
        default=ROOT / "data_candidate" / "territorial_intelligence",
    )
    args = parser.parse_args()

    if not args.input.exists():
        raise FileNotFoundError(f"Inteligência territorial não encontrada: {args.input}")

    territorial = pd.read_csv(args.input, dtype={"codigo_ibge": "string"})
    cards = build_review_cards(territorial)

    if len(cards) != 142 or cards["codigo_ibge"].nunique() != 142:
        raise ValueError("Cards de revisão devem cobrir exatamente os 142 municípios.")

    args.out_dir.mkdir(parents=True, exist_ok=True)
    csv_path = args.out_dir / "territorial_review_cards_v2_1.csv"
    meta_path = args.out_dir / "territorial_review_cards_v2_1.metadata.json"
    cards.to_csv(csv_path, index=False, encoding="utf-8")

    metadata = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "rows": int(len(cards)),
        "status": "experimental_explainable_review",
        "human_review_required": True,
        "operational_recommendation_enabled": False,
        "composite_score_used": False,
    }
    meta_path.write_text(
        json.dumps(metadata, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    print(json.dumps(metadata, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
