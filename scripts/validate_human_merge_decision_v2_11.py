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

from src.human_merge_record_v2_11 import (
    load_merge_record_config,
    validate_human_merge_decisions,
)


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Valida decisões humanas de merge v2.11."
    )
    parser.add_argument("--input", type=Path, required=True)
    parser.add_argument(
        "--gate",
        type=Path,
        default=ROOT / "data_candidate" / "merge_gate_v2_10" / "merge_gate_validated_v2_10.csv",
    )
    parser.add_argument(
        "--config",
        type=Path,
        default=ROOT / "config" / "human_merge_record_v2_11.json",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=ROOT / "data_candidate" / "human_merge_v2_11" / "human_merge_decisions_validated_v2_11.csv",
    )
    args = parser.parse_args()

    for path in (args.input, args.gate, args.config):
        if not path.exists():
            raise FileNotFoundError(path)

    decisions = pd.read_csv(args.input)
    gate = pd.read_csv(args.gate)
    config = load_merge_record_config(args.config)

    validated = validate_human_merge_decisions(
        decisions,
        gate,
        config,
    )

    args.output.parent.mkdir(parents=True, exist_ok=True)
    validated.to_csv(args.output, index=False, encoding="utf-8")

    summary = {
        "records": int(len(validated)),
        "approve_human_merge": int(
            (validated["merge_decision"] == "approve_human_merge").sum()
        ),
        "reject_merge": int(
            (validated["merge_decision"] == "reject_merge").sum()
        ),
        "defer_merge": int(
            (validated["merge_decision"] == "defer_merge").sum()
        ),
        "merge_decision_is_not_merge_execution": True,
        "automatic_merge_enabled": False,
        "automatic_deploy_enabled": False,
        "automatic_rollback_enabled": False,
    }
    print(json.dumps(summary, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
