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

from src.postmortem_learning_v2_14 import (
    load_postmortem_config,
    validate_postmortem_records,
)


def read_optional(path: Path) -> pd.DataFrame | None:
    return pd.read_csv(path) if path.exists() else None


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Valida registros de post-mortem e aprendizado v2.14."
    )
    parser.add_argument("--input", type=Path, required=True)
    parser.add_argument(
        "--effects",
        type=Path,
        default=ROOT / "data_candidate" / "deployment_v2_12" / "effect_verification_validated_v2_12.csv",
    )
    parser.add_argument(
        "--rollbacks",
        type=Path,
        default=ROOT / "data_candidate" / "rollback_v2_13" / "rollback_execution_validated_v2_13.csv",
    )
    parser.add_argument(
        "--config",
        type=Path,
        default=ROOT / "config" / "postmortem_learning_v2_14.json",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=ROOT / "data_candidate" / "postmortem_v2_14" / "postmortem_validated_v2_14.csv",
    )
    args = parser.parse_args()

    for path in (args.input, args.config):
        if not path.exists():
            raise FileNotFoundError(path)

    records = pd.read_csv(args.input)
    effects = read_optional(args.effects)
    rollbacks = read_optional(args.rollbacks)
    cfg = load_postmortem_config(args.config)

    out = validate_postmortem_records(
        records,
        effects,
        rollbacks,
        cfg,
    )

    args.output.parent.mkdir(parents=True, exist_ok=True)
    out.to_csv(args.output, index=False, encoding="utf-8")

    summary = {
        "records": int(len(out)),
        "closed": int((out["postmortem_status"] == "closed").sum()),
        "reenter_rule_review": int(
            out["reenter_rule_review"].astype(bool).sum()
        ),
        "postmortem_is_not_causal_proof": True,
        "learning_is_not_rule_change": True,
        "automatic_rule_change_enabled": False,
        "automatic_issue_creation_enabled": False,
    }
    print(json.dumps(summary, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
