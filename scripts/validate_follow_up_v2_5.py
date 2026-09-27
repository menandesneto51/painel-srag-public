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

from src.decision_audit_v2_5 import load_decision_config
from src.decision_followup_v2_5 import (
    build_follow_up_status,
    validate_follow_up_events,
)


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Valida eventos de follow-up v2.5 e constrói estado temporal."
    )
    parser.add_argument("--events", type=Path, required=True)
    parser.add_argument(
        "--decisions",
        type=Path,
        default=ROOT / "data_candidate" / "decision_audit_v2_5" / "human_decisions_validated_v2_5.csv",
    )
    parser.add_argument(
        "--config",
        type=Path,
        default=ROOT / "config" / "decision_audit_v2_5.json",
    )
    parser.add_argument("--as-of", required=True)
    parser.add_argument(
        "--out-dir",
        type=Path,
        default=ROOT / "data_candidate" / "decision_audit_v2_5",
    )
    args = parser.parse_args()

    for path in (args.events, args.decisions, args.config):
        if not path.exists():
            raise FileNotFoundError(path)

    events = pd.read_csv(args.events)
    decisions = pd.read_csv(args.decisions, dtype={"codigo_ibge": "string"})
    config = load_decision_config(args.config)

    validated_events = validate_follow_up_events(
        events,
        decisions,
        set(config["follow_up_event_statuses"]),
    )
    status = build_follow_up_status(
        decisions,
        validated_events,
        as_of=args.as_of,
    )

    args.out_dir.mkdir(parents=True, exist_ok=True)
    events_path = args.out_dir / "follow_up_events_validated_v2_5.csv"
    status_path = args.out_dir / "follow_up_status_v2_5.csv"
    validated_events.to_csv(events_path, index=False, encoding="utf-8")
    status.to_csv(status_path, index=False, encoding="utf-8")

    summary = {
        "events": int(len(validated_events)),
        "decisions": int(len(decisions)),
        "follow_up_open": int((status["follow_up_state"] == "open").sum()),
        "follow_up_overdue": int((status["follow_up_state"] == "overdue").sum()),
        "follow_up_completed": int((status["follow_up_state"] == "completed").sum()),
        "follow_up_cancelled": int((status["follow_up_state"] == "cancelled").sum()),
        "automatic_execution_enabled": False,
        "follow_up_state_is_not_risk": True,
    }
    print(json.dumps(summary, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
