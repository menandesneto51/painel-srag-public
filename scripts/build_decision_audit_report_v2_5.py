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

from src.decision_audit_report_v2_5 import (
    build_decision_audit_summary,
    render_decision_audit_markdown,
)


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Gera relatório estadual da auditoria de decisões humanas v2.5."
    )
    parser.add_argument(
        "--decisions",
        type=Path,
        default=ROOT / "data_candidate" / "decision_audit_v2_5" / "human_decisions_validated_v2_5.csv",
    )
    parser.add_argument(
        "--follow-up-status",
        type=Path,
        default=ROOT / "data_candidate" / "decision_audit_v2_5" / "follow_up_status_v2_5.csv",
    )
    parser.add_argument(
        "--out-dir",
        type=Path,
        default=ROOT / "data_candidate" / "decision_audit_v2_5",
    )
    args = parser.parse_args()

    if not args.decisions.exists():
        raise FileNotFoundError(args.decisions)

    decisions = pd.read_csv(
        args.decisions, dtype={"codigo_ibge": "string"}
    )
    follow_up = (
        pd.read_csv(
            args.follow_up_status,
            dtype={"codigo_ibge": "string"},
        )
        if args.follow_up_status.exists()
        else None
    )

    summary = build_decision_audit_summary(decisions, follow_up)
    report = render_decision_audit_markdown(decisions, follow_up)

    args.out_dir.mkdir(parents=True, exist_ok=True)
    summary_path = args.out_dir / "decision_audit_summary_v2_5.json"
    report_path = args.out_dir / "decision_audit_report_v2_5.md"
    summary_path.write_text(
        json.dumps(summary, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    report_path.write_text(report, encoding="utf-8")

    print(json.dumps(summary, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
