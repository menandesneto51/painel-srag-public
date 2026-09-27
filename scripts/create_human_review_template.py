# -*- coding: utf-8 -*-
from __future__ import annotations

import argparse
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Gera template para registro humano de decisões da fila v2.2."
    )
    parser.add_argument(
        "--queue",
        type=Path,
        default=(
            ROOT
            / "data_candidate"
            / "operational_review"
            / "operational_review_queue_v2_2.csv"
        ),
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=(
            ROOT
            / "data_candidate"
            / "operational_review"
            / "human_review_decisions_template.csv"
        ),
    )
    args = parser.parse_args()

    if not args.queue.exists():
        raise FileNotFoundError(args.queue)

    queue = pd.read_csv(args.queue, dtype={"codigo_ibge": "string"})
    required = {"codigo_ibge", "municipio", "review_queue"}
    missing = required.difference(queue.columns)
    if missing:
        raise ValueError(f"Fila sem colunas: {sorted(missing)}")

    template = queue[["codigo_ibge", "municipio", "review_queue"]].copy()
    template["reviewed_at"] = ""
    template["reviewer_role"] = ""
    template["decision_status"] = ""
    template["rationale"] = ""
    template["evidence_refs"] = ""
    template["notes"] = ""

    args.output.parent.mkdir(parents=True, exist_ok=True)
    template.to_csv(args.output, index=False, encoding="utf-8")
    print(f"rows={len(template)}")
    print(f"output={args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
