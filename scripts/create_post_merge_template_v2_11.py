# -*- coding: utf-8 -*-
from __future__ import annotations

import argparse
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Gera template pós-merge v2.11 apenas para decisões humanas aprovadas."
    )
    parser.add_argument(
        "--decisions",
        type=Path,
        default=ROOT / "data_candidate" / "human_merge_v2_11" / "human_merge_decisions_validated_v2_11.csv",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=ROOT / "data_candidate" / "human_merge_v2_11" / "post_merge_template_v2_11.csv",
    )
    args = parser.parse_args()

    if not args.decisions.exists():
        raise FileNotFoundError(args.decisions)

    decisions = pd.read_csv(args.decisions)
    approved = decisions.loc[
        decisions["merge_decision"]
        .astype(str)
        .eq("approve_human_merge")
    ].copy()

    template = approved[[
        "merge_decision_record_id",
        "merge_gate_record_id",
        "implementation_package_id",
        "implementation_branch",
        "implementation_commit_sha",
    ]].copy()

    for col in (
        "recorded_at",
        "reviewer_role",
        "merged_commit_sha",
        "merge_evidence_ref",
        "post_merge_ci_status",
        "smoke_test_status",
        "epidemiology_sanity_status",
        "security_privacy_check_status",
        "rollback_readiness_status",
        "post_merge_state",
        "verification_notes",
    ):
        template[col] = ""

    args.output.parent.mkdir(parents=True, exist_ok=True)
    template.to_csv(args.output, index=False, encoding="utf-8")
    print(f"rows={len(template)}")
    print(f"output={args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
