# -*- coding: utf-8 -*-
from __future__ import annotations

import argparse
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Gera template de follow-up apenas para decisões que o exigem."
    )
    parser.add_argument(
        "--decisions",
        type=Path,
        default=ROOT / "data_candidate" / "decision_audit_v2_5" / "human_decisions_validated_v2_5.csv",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=ROOT / "data_candidate" / "decision_audit_v2_5" / "follow_up_events_template_v2_5.csv",
    )
    args = parser.parse_args()

    if not args.decisions.exists():
        raise FileNotFoundError(args.decisions)

    decisions = pd.read_csv(args.decisions, dtype={"codigo_ibge": "string"})
    required = {
        "decision_record_id",
        "codigo_ibge",
        "municipio",
        "follow_up_required",
        "follow_up_due_at",
        "follow_up_owner_role",
    }
    missing = required.difference(decisions.columns)
    if missing:
        raise ValueError(f"Decisões validadas sem colunas: {sorted(missing)}")

    required_follow = decisions.loc[
        decisions["follow_up_required"].astype(str).str.lower().isin(
            {"true", "1", "yes", "sim"}
        )
    ].copy()

    template = required_follow[[
        "decision_record_id",
        "codigo_ibge",
        "municipio",
        "follow_up_due_at",
        "follow_up_owner_role",
    ]].copy()
    template["event_at"] = ""
    template["reviewer_role"] = ""
    template["follow_up_event_status"] = ""
    template["follow_up_note"] = ""
    template["evidence_refs"] = ""

    args.output.parent.mkdir(parents=True, exist_ok=True)
    template.to_csv(args.output, index=False, encoding="utf-8")
    print(f"rows={len(template)}")
    print(f"output={args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
