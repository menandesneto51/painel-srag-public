# -*- coding: utf-8 -*-
from __future__ import annotations

import argparse
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Gera template de registro de deploy v2.12."
    )
    parser.add_argument(
        "--decisions",
        type=Path,
        default=ROOT / "data_candidate" / "deployment_v2_12" / "human_deploy_decisions_validated_v2_12.csv",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=ROOT / "data_candidate" / "deployment_v2_12" / "deployment_record_template_v2_12.csv",
    )
    args = parser.parse_args()

    if not args.decisions.exists():
        raise FileNotFoundError(args.decisions)

    decisions = pd.read_csv(args.decisions)
    approved = decisions.loc[
        decisions["deploy_decision"].astype(str).eq("approve_human_deploy")
    ].copy()

    template = approved[[
        "deploy_decision_record_id",
        "implementation_package_id",
        "merged_commit_sha",
    ]].copy()
    for col in (
        "deployed_at",
        "reviewer_role",
        "environment",
        "deployed_commit_sha",
        "deploy_evidence_ref",
        "post_deploy_ci_status",
        "smoke_test_status",
        "health_check_status",
        "security_privacy_check_status",
        "rollback_readiness_status",
        "deployment_state",
        "deployment_notes",
    ):
        template[col] = ""

    args.output.parent.mkdir(parents=True, exist_ok=True)
    template.to_csv(args.output, index=False, encoding="utf-8")
    print(f"rows={len(template)}")
    print(f"output={args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
