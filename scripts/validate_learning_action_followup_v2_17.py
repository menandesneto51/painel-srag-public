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

from src.learning_action_followup_v2_17 import (
    load_learning_action_followup_config,
    validate_learning_action_followup,
)


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Valida follow-up das ações de aprendizado v2.17."
    )
    parser.add_argument("--input", type=Path, required=True)
    parser.add_argument("--as-of", required=True)
    parser.add_argument(
        "--postmortems",
        type=Path,
        default=ROOT / "data_candidate" / "postmortem_v2_14" / "postmortem_validated_v2_14.csv",
    )
    parser.add_argument(
        "--config",
        type=Path,
        default=ROOT / "config" / "learning_action_followup_v2_17.json",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=ROOT / "data_candidate" / "learning_action_followup_v2_17" / "learning_action_followup_validated_v2_17.csv",
    )
    args = parser.parse_args()

    for path in (args.input, args.postmortems, args.config):
        if not path.exists():
            raise FileNotFoundError(path)

    records = pd.read_csv(args.input)
    postmortems = pd.read_csv(args.postmortems)
    config = load_learning_action_followup_config(args.config)

    out = validate_learning_action_followup(
        records,
        postmortems,
        config,
        args.as_of,
    )

    args.output.parent.mkdir(parents=True, exist_ok=True)
    out.to_csv(args.output, index=False, encoding="utf-8")

    summary = {
        "actions": int(len(out)),
        "overdue": int(out["overdue"].astype(bool).sum()) if not out.empty else 0,
        "verified_closed": int(
            out["follow_up_state"].astype(str).eq("verified_closed").sum()
        ) if not out.empty else 0,
        "completion_is_not_effectiveness_proof": True,
        "overdue_is_not_risk": True,
        "automatic_execution_enabled": False,
        "automatic_issue_creation_enabled": False,
        "automatic_rule_change_enabled": False,
    }
    print(json.dumps(summary, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
