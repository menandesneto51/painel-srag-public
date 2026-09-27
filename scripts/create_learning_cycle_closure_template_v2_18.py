# -*- coding: utf-8 -*-
from __future__ import annotations

import argparse
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Gera template do gate de encerramento v2.18."
    )
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
        "--output",
        type=Path,
        default=ROOT / "data_candidate" / "learning_cycle_closure_v2_18" / "learning_cycle_closure_template_v2_18.csv",
    )
    args = parser.parse_args()

    if not args.postmortems.exists():
        raise FileNotFoundError(args.postmortems)

    postmortems = pd.read_csv(args.postmortems)
    actions = pd.read_csv(args.actions) if args.actions.exists() else None

    eligible = postmortems.loc[
        postmortems["postmortem_status"].astype(str).eq("closed")
        & ~postmortems["learning_action_type"].astype(str).eq("none")
    ].copy()

    rows = []
    for row in eligible.to_dict(orient="records"):
        pid = row["postmortem_record_id"]
        action_count = 0
        if actions is not None and "postmortem_record_id" in actions.columns:
            action_count = int(
                actions["postmortem_record_id"].astype(str).eq(str(pid)).sum()
            )
        rows.append({
            "postmortem_record_id": pid,
            "implementation_package_id": row["implementation_package_id"],
            "learning_action_type": row["learning_action_type"],
            "action_count_context": action_count,
            "evaluated_at": "",
            "reviewer_role": "",
            "action_coverage_review_status": "",
            "evidence_review_status": "",
            "rule_handoff_review_status": (
                "" if str(row["learning_action_type"]) == "rule_review"
                else "not_applicable"
            ),
            "closure_decision": "",
            "decision_rationale": "",
            "closure_evidence_refs": "",
        })

    args.output.parent.mkdir(parents=True, exist_ok=True)
    pd.DataFrame(rows).to_csv(
        args.output, index=False, encoding="utf-8"
    )
    print(f"rows={len(rows)}")
    print(f"output={args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
