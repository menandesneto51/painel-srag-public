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

from src.human_review_decisions import validate_review_decisions


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Valida registro humano de decisões da revisão v2.2."
    )
    parser.add_argument("--input", type=Path, required=True)
    parser.add_argument(
        "--output",
        type=Path,
        default=(
            ROOT
            / "data_candidate"
            / "operational_review"
            / "human_review_decisions_validated.csv"
        ),
    )
    args = parser.parse_args()

    frame = pd.read_csv(args.input, dtype={"codigo_ibge": "string"})
    validated = validate_review_decisions(frame)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    validated.to_csv(args.output, index=False, encoding="utf-8")

    summary = {
        "rows": int(len(validated)),
        "municipalities": int(validated["codigo_ibge"].nunique()),
        "decision_recorded_by_human": True,
        "automatic_execution_enabled": False,
        "patient_level_decision_enabled": False,
    }
    print(json.dumps(summary, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
