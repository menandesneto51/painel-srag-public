# -*- coding: utf-8 -*-
from __future__ import annotations

import argparse
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Gera template de follow-up v2.17 a partir do post-mortem v2.14."
    )
    parser.add_argument(
        "--postmortems",
        type=Path,
        default=ROOT / "data_candidate" / "postmortem_v2_14" / "postmortem_validated_v2_14.csv",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=ROOT / "data_candidate" / "learning_action_followup_v2_17" / "learning_action_followup_template_v2_17.csv",
    )
    args = parser.parse_args()

    if not args.postmortems.exists():
        raise FileNotFoundError(args.postmortems)

    postmortems = pd.read_csv(args.postmortems)
    required = {
        "postmortem_record_id",
        "implementation_package_id",
        "postmortem_status",
        "learning_action_type",
        "follow_up_actions",
        "reenter_rule_review",
        "rule_review_scope",
    }
    missing = required.difference(postmortems.columns)
    if missing:
        raise ValueError(
            f"Post-mortem v2.14 sem colunas: {sorted(missing)}"
        )

    eligible = postmortems.loc[
        postmortems["postmortem_status"].astype(str).isin({"in_review", "closed"})
        & ~postmortems["learning_action_type"].astype(str).eq("none")
    ].copy()

    rows = []
    for row in eligible.to_dict(orient="records"):
        rows.append({
            "postmortem_record_id": row["postmortem_record_id"],
            "implementation_package_id": row["implementation_package_id"],
            "learning_action_type": row["learning_action_type"],
            "action_sequence": 1,
            "action_description": row["follow_up_actions"],
            "owner_role": "",
            "created_at": "",
            "due_at": "",
            "action_status": "planned",
            "status_updated_at": "",
            "completed_at": "",
            "completion_evidence_refs": "",
            "verification_status": "not_started",
            "verified_at": "",
            "verifier_role": "",
            "verification_notes": "",
            "blocking_reason": "",
            "cancellation_rationale": "",
            "governance_handoff_ref": "",
            "reenter_rule_review": row["reenter_rule_review"],
            "rule_review_scope": row["rule_review_scope"],
        })

    template_columns = [
        "postmortem_record_id",
        "implementation_package_id",
        "learning_action_type",
        "action_sequence",
        "action_description",
        "owner_role",
        "created_at",
        "due_at",
        "action_status",
        "status_updated_at",
        "completed_at",
        "completion_evidence_refs",
        "verification_status",
        "verified_at",
        "verifier_role",
        "verification_notes",
        "blocking_reason",
        "cancellation_rationale",
        "governance_handoff_ref",
        "reenter_rule_review",
        "rule_review_scope",
    ]
    template = pd.DataFrame(rows, columns=template_columns)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    template.to_csv(args.output, index=False, encoding="utf-8")
    print(f"rows={len(template)}")
    print(f"output={args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
