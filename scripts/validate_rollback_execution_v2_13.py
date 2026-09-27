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

from src.rollback_governance_v2_13 import (
    load_rollback_config,
    validate_rollback_execution_records,
)


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Valida execução humana de rollback v2.13."
    )
    parser.add_argument("--input", type=Path, required=True)
    parser.add_argument(
        "--decisions",
        type=Path,
        default=ROOT / "data_candidate" / "rollback_v2_13" / "human_rollback_decisions_validated_v2_13.csv",
    )
    parser.add_argument(
        "--config",
        type=Path,
        default=ROOT / "config" / "rollback_governance_v2_13.json",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=ROOT / "data_candidate" / "rollback_v2_13" / "rollback_execution_validated_v2_13.csv",
    )
    args = parser.parse_args()

    for path in (args.input, args.decisions, args.config):
        if not path.exists():
            raise FileNotFoundError(path)

    records = pd.read_csv(args.input)
    decisions = pd.read_csv(args.decisions)
    cfg = load_rollback_config(args.config)

    out = validate_rollback_execution_records(records, decisions, cfg)

    args.output.parent.mkdir(parents=True, exist_ok=True)
    out.to_csv(args.output, index=False, encoding="utf-8")

    summary = {
        "records": int(len(out)),
        "verified_restored": int(
            (out["rollback_execution_state"] == "verified_restored").sum()
        ),
        "needs_investigation": int(
            (out["rollback_execution_state"] == "needs_investigation").sum()
        ),
        "rollback_record_requires_actual_rollback_evidence": True,
        "automatic_rollback_enabled": False,
    }
    print(json.dumps(summary, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
