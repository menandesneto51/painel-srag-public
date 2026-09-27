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
        default=(
            ROOT
            / "data_candidate"
            / "deployment_v2_12"
            / "human_deploy_decisions_validated_v2_12.csv"
        ),
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=(
            ROOT
            / "data_candidate"
            / "deployment_v2_12"
            / "deployment_record_template_v2_12.csv"
        ),
    )
    args = parser.parse_args()

    if not args.decisions.exists():
        raise FileNotFoundError(args.decisions)

    decisions = pd.read_csv(args.decisions)
    required = {
        "deploy_decision_record_id",
        "release_gate_record_id",
        "implementation_package_id",
        "release_commit_sha",
        "target_environment",
        "deploy_decision",
    }
    missing = required.difference(decisions.columns)
    if missing:
        raise ValueError(
            f"Decisões de deploy v2.12 sem colunas: {sorted(missing)}"
        )

    approved = decisions.loc[
        decisions["deploy_decision"]
        .astype(str)
        .eq("approve_human_deploy")
    ].copy()

    template = approved[[
        "deploy_decision_record_id",
        "release_gate_record_id",
        "implementation_package_id",
        "release_commit_sha",
        "target_environment",
    ]].copy()
    template["deployed_at"] = ""
    template["reviewer_role"] = ""
    template["environment"] = template["target_environment"]
    template["deployed_commit_sha"] = template["release_commit_sha"]
    template["deploy_evidence_ref"] = ""
    template["post_deploy_ci_status"] = ""
    template["smoke_test_status"] = ""
    template["health_check_status"] = ""
    template["security_privacy_check_status"] = ""
    template["rollback_readiness_status"] = ""
    template["deployment_state"] = ""
    template["deployment_notes"] = ""

    args.output.parent.mkdir(parents=True, exist_ok=True)
    template.to_csv(args.output, index=False, encoding="utf-8")
    print(f"rows={len(template)}")
    print(f"output={args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
