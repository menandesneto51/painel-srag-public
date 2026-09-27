# -*- coding: utf-8 -*-
from __future__ import annotations

import argparse
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Gera template de execução de rollback v2.13."
    )
    parser.add_argument(
        "--decisions",
        type=Path,
        default=ROOT / "data_candidate" / "rollback_v2_13" / "human_rollback_decisions_validated_v2_13.csv",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=ROOT / "data_candidate" / "rollback_v2_13" / "rollback_execution_template_v2_13.csv",
    )
    args = parser.parse_args()

    if not args.decisions.exists():
        raise FileNotFoundError(args.decisions)

    decisions = pd.read_csv(args.decisions)
    approved = decisions.loc[
        decisions["rollback_decision"].astype(str).eq("approve_human_rollback")
    ].copy()

    template = approved[[
        "rollback_decision_record_id",
        "implementation_package_id",
        "rollback_target_commit_sha",
    ]].copy()

    for col in (
        "rolled_back_at",
        "reviewer_role",
        "rolled_back_commit_sha",
        "rollback_evidence_ref",
        "post_rollback_ci_status",
        "smoke_test_status",
        "health_check_status",
        "security_privacy_check_status",
        "epidemiology_sanity_status",
        "rollback_execution_state",
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
