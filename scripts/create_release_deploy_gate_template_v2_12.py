# -*- coding: utf-8 -*-
from __future__ import annotations

import argparse
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Gera template do gate de release/deploy v2.12."
    )
    parser.add_argument(
        "--post-merge",
        type=Path,
        default=(
            ROOT
            / "data_candidate"
            / "human_merge_v2_11"
            / "post_merge_records_validated_v2_11.csv"
        ),
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=(
            ROOT
            / "data_candidate"
            / "release_deploy_gate_v2_12"
            / "release_deploy_gate_template_v2_12.csv"
        ),
    )
    args = parser.parse_args()

    if not args.post_merge.exists():
        raise FileNotFoundError(args.post_merge)

    post = pd.read_csv(args.post_merge)
    required = {
        "post_merge_record_id",
        "merge_decision_record_id",
        "merge_gate_record_id",
        "implementation_package_id",
        "merged_commit_sha",
        "post_merge_state",
        "rollback_readiness_status",
    }
    missing = required.difference(post.columns)
    if missing:
        raise ValueError(f"Pós-merge v2.11 sem colunas: {sorted(missing)}")

    healthy = post.loc[
        post["post_merge_state"].astype(str).eq("verified_healthy")
        & post["rollback_readiness_status"].astype(str).eq("ready")
    ].copy()

    template = healthy[[
        "post_merge_record_id",
        "merge_decision_record_id",
        "merge_gate_record_id",
        "implementation_package_id",
        "merged_commit_sha",
    ]].rename(columns={"merged_commit_sha": "release_commit_sha"})

    template["evaluated_at"] = ""
    template["reviewer_role"] = ""
    template["target_environment"] = ""
    template["release_version"] = ""
    template["release_notes_ref"] = ""
    template["deployment_plan_ref"] = ""
    template["monitoring_plan_ref"] = ""
    template["rollback_plan_ref"] = ""
    template["predeploy_ci_status"] = ""
    template["predeploy_security_privacy_status"] = ""
    template["monitoring_readiness_status"] = ""
    template["rollback_plan_verification_status"] = ""
    template["change_window_status"] = ""
    template["final_release_decision"] = ""
    template["release_rationale"] = ""

    args.output.parent.mkdir(parents=True, exist_ok=True)
    template.to_csv(args.output, index=False, encoding="utf-8")
    print(f"rows={len(template)}")
    print(f"output={args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
