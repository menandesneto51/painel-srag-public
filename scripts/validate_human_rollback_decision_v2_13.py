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
    validate_human_rollback_decisions,
)


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Valida decisões humanas de rollback v2.13."
    )
    parser.add_argument("--input", type=Path, required=True)
    parser.add_argument(
        "--deployments",
        type=Path,
        default=ROOT / "data_candidate" / "deployment_v2_12" / "deployment_records_validated_v2_12.csv",
    )
    parser.add_argument(
        "--effects",
        type=Path,
        default=ROOT / "data_candidate" / "deployment_v2_12" / "effect_verification_validated_v2_12.csv",
    )
    parser.add_argument(
        "--config",
        type=Path,
        default=ROOT / "config" / "rollback_governance_v2_13.json",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=ROOT / "data_candidate" / "rollback_v2_13" / "human_rollback_decisions_validated_v2_13.csv",
    )
    args = parser.parse_args()

    for path in (args.input, args.deployments, args.config):
        if not path.exists():
            raise FileNotFoundError(path)

    decisions = pd.read_csv(args.input)
    deployments = pd.read_csv(args.deployments)
    effects = pd.read_csv(args.effects) if args.effects.exists() else None
    cfg = load_rollback_config(args.config)

    out = validate_human_rollback_decisions(
        decisions, deployments, effects, cfg
    )

    args.output.parent.mkdir(parents=True, exist_ok=True)
    out.to_csv(args.output, index=False, encoding="utf-8")

    summary = {
        "records": int(len(out)),
        "approved": int((out["rollback_decision"] == "approve_human_rollback").sum()),
        "rejected": int((out["rollback_decision"] == "reject_rollback").sum()),
        "deferred": int((out["rollback_decision"] == "defer_rollback").sum()),
        "rollback_decision_is_not_rollback_execution": True,
        "automatic_rollback_enabled": False,
    }
    print(json.dumps(summary, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
