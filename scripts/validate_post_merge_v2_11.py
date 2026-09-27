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
    validate_post_merge_records,
)


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Valida registros humanos pós-merge v2.11."
    )
    parser.add_argument("--input", type=Path, required=True)
    parser.add_argument(
        "--decisions",
        type=Path,
        default=(
            ROOT
            / "data_candidate"
            / "human_merge_v2_11"
            / "human_merge_decisions_validated_v2_11.csv"
        ),
    )
    parser.add_argument(
        "--config",
        type=Path,
        default=ROOT / "config" / "human_merge_record_v2_11.json",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=(
            ROOT
            / "data_candidate"
            / "human_merge_v2_11"
            / "post_merge_records_validated_v2_11.csv"
        ),
    )
    args = parser.parse_args()

    for path in (args.input, args.decisions, args.config):
        if not path.exists():
            raise FileNotFoundError(path)

    records = pd.read_csv(args.input)
    decisions = pd.read_csv(args.decisions)
    config = load_merge_record_config(args.config)

    validated = validate_post_merge_records(
        records,
        decisions,
        config,
    )

    args.output.parent.mkdir(parents=True, exist_ok=True)
    validated.to_csv(args.output, index=False, encoding="utf-8")

    summary = {
        "records": int(len(validated)),
        "verified_healthy": int(
            (validated["post_merge_state"] == "verified_healthy").sum()
        ),
        "needs_investigation": int(
            (validated["post_merge_state"] == "needs_investigation").sum()
        ),
        "rollback_consideration": int(
            (validated["post_merge_state"] == "rollback_consideration").sum()
        ),
        "post_merge_record_requires_actual_merge_evidence": True,
        "post_merge_record_is_not_deploy": True,
        "automatic_merge_enabled": False,
        "automatic_deploy_enabled": False,
        "automatic_rollback_enabled": False,
    }
    print(json.dumps(summary, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
