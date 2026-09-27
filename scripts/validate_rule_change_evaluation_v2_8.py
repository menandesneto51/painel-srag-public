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

from src.rule_change_evaluation_v2_8 import (
    load_evaluation_config,
    validate_rule_change_evaluations,
)


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Valida avaliação formal humana das propostas v2.7 — v2.8."
    )
    parser.add_argument("--input", type=Path, required=True)
    parser.add_argument(
        "--proposals",
        type=Path,
        default=ROOT / "data_candidate" / "rule_change_proposals_v2_7" / "rule_change_proposals_v2_7.csv",
    )
    parser.add_argument(
        "--config",
        type=Path,
        default=ROOT / "config" / "rule_change_evaluation_v2_8.json",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=ROOT / "data_candidate" / "rule_change_evaluation_v2_8" / "rule_change_evaluations_validated_v2_8.csv",
    )
    args = parser.parse_args()

    for path in (args.input, args.proposals, args.config):
        if not path.exists():
            raise FileNotFoundError(path)

    evaluations = pd.read_csv(args.input)
    proposals = pd.read_csv(args.proposals)
    config = load_evaluation_config(args.config)

    validated = validate_rule_change_evaluations(
        evaluations,
        proposals,
        config,
    )
    args.output.parent.mkdir(parents=True, exist_ok=True)
    validated.to_csv(args.output, index=False, encoding="utf-8")

    summary = {
        "evaluations": int(len(validated)),
        "approved_for_implementation_branch": int(
            (validated["final_decision"] == "approve_for_implementation_branch").sum()
        ),
        "rejected": int((validated["final_decision"] == "reject").sum()),
        "deferred": int((validated["final_decision"] == "defer").sum()),
        "automatic_rule_change_enabled": False,
        "automatic_threshold_change_enabled": False,
        "automatic_merge_enabled": False,
        "automatic_deploy_enabled": False,
        "decision_is_not_implementation": True,
    }
    print(json.dumps(summary, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
