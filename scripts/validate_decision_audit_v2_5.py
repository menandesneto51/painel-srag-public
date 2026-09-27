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

from src.decision_audit_v2_5 import load_decision_config, validate_decision_audit


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Valida decisões humanas v2.5 contra fila e ações de origem."
    )
    parser.add_argument("--input", type=Path, required=True)
    parser.add_argument(
        "--queue",
        type=Path,
        default=ROOT / "data_candidate" / "operational_v2_2" / "municipal_review_queue_v2_2.csv",
    )
    parser.add_argument(
        "--actions",
        type=Path,
        default=ROOT / "data_candidate" / "operational_v2_2" / "operational_action_suggestions_v2_2.csv",
    )
    parser.add_argument(
        "--config",
        type=Path,
        default=ROOT / "config" / "decision_audit_v2_5.json",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=ROOT / "data_candidate" / "decision_audit_v2_5" / "human_decisions_validated_v2_5.csv",
    )
    args = parser.parse_args()

    for path in (args.input, args.queue, args.config):
        if not path.exists():
            raise FileNotFoundError(path)

    decisions = pd.read_csv(args.input, dtype={"codigo_ibge": "string"})
    queue = pd.read_csv(args.queue, dtype={"codigo_ibge": "string"})
    actions = (
        pd.read_csv(args.actions, dtype={"codigo_ibge": "string"})
        if args.actions.exists()
        else None
    )
    config = load_decision_config(args.config)

    validated = validate_decision_audit(
        decisions,
        queue,
        actions,
        config,
    )

    args.output.parent.mkdir(parents=True, exist_ok=True)
    validated.to_csv(args.output, index=False, encoding="utf-8")

    summary = {
        "rows": int(len(validated)),
        "municipalities": int(validated["codigo_ibge"].nunique()),
        "decisions_with_follow_up": int(validated["follow_up_required"].sum()),
        "automatic_execution_enabled": False,
        "patient_level_decision_enabled": False,
        "clinical_prescription_enabled": False,
        "decision_is_not_proof_of_execution": True,
    }
    print(json.dumps(summary, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
