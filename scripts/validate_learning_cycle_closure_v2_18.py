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

from src.learning_cycle_closure_v2_18 import (
    load_learning_cycle_closure_config,
    validate_learning_cycle_closure,
)


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Valida decisão humana de encerramento do ciclo de aprendizado v2.18."
    )
    parser.add_argument("--input", type=Path, required=True)
    parser.add_argument(
        "--postmortems",
        type=Path,
        default=ROOT / "data_candidate" / "postmortem_v2_14" / "postmortem_validated_v2_14.csv",
    )
    parser.add_argument(
        "--actions",
        type=Path,
        default=ROOT / "data_candidate" / "learning_action_followup_v2_17" / "learning_action_followup_validated_v2_17.csv",
    )
    parser.add_argument(
        "--config",
        type=Path,
        default=ROOT / "config" / "learning_cycle_closure_v2_18.json",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=ROOT / "data_candidate" / "learning_cycle_closure_v2_18" / "learning_cycle_closure_validated_v2_18.csv",
    )
    args = parser.parse_args()

    for path in (
        args.input,
        args.postmortems,
        args.actions,
        args.config,
    ):
        if not path.exists():
            raise FileNotFoundError(path)

    records = pd.read_csv(args.input)
    postmortems = pd.read_csv(args.postmortems)
    actions = pd.read_csv(args.actions)
    config = load_learning_cycle_closure_config(args.config)

    out = validate_learning_cycle_closure(
        records, postmortems, actions, config
    )
    args.output.parent.mkdir(parents=True, exist_ok=True)
    out.to_csv(args.output, index=False, encoding="utf-8")

    summary = {
        "records": int(len(out)),
        "closed": int(
            out["learning_cycle_state"]
            .astype(str)
            .eq("learning_cycle_closed_human")
            .sum()
        ) if not out.empty else 0,
        "postmortem_closed_is_not_learning_cycle_closed": True,
        "closure_is_not_epidemiological_effect": True,
        "automatic_closure_enabled": False,
    }
    print(json.dumps(summary, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
