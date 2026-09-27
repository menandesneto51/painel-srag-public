# -*- coding: utf-8 -*-
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

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
        description="Gera fila explicável de revisão e relatório estadual SRAG v2.2."
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
        "--config",
        type=Path,
        default=ROOT / "config" / "operational_review_v2_2.json",
    )
    parser.add_argument(
        "--out-dir",
        type=Path,
        default=ROOT / "data_candidate" / "operational_review",
    )
    args = parser.parse_args()

    if not args.cards.exists():
        raise FileNotFoundError(f"Cards v2.1 ausentes: {args.cards}")

    cards = pd.read_csv(args.cards, dtype={"codigo_ibge": "string"})
    config = load_operational_config(args.config)
    queue = build_operational_review_queue(cards, config)

    if len(queue) != 142 or queue["codigo_ibge"].nunique() != 142:
        raise ValueError("Fila v2.2 deve cobrir exatamente os 142 municípios.")

    summary = build_state_review_summary(queue)
    report = render_state_review_markdown(queue)

    args.out_dir.mkdir(parents=True, exist_ok=True)
    queue.to_csv(
        args.out_dir / "operational_review_queue_v2_2.csv",
        index=False,
        encoding="utf-8",
    )
    (args.out_dir / "state_review_summary_v2_2.json").write_text(
        json.dumps(summary, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    (args.out_dir / "state_review_report_v2_2.md").write_text(
        report,
        encoding="utf-8",
    )

    print(json.dumps(summary, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
