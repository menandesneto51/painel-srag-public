# -*- coding: utf-8 -*-
from __future__ import annotations

import argparse
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Gera template de decisão humana de rollback v2.13."
    )
    parser.add_argument(
        "--deployments",
        type=Path,
        default=ROOT / "data_candidate" / "deployment_v2_12" / "deployment_records_validated_v2_12.csv",
    )
    parser.add_argument(
        "--effects",
        type=Path,
        default=ROOT / "data_candidate" / "deployment_v2_12" / "effect_verification_validated_v2_12.csv",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=ROOT / "data_candidate" / "rollback_v2_13" / "human_rollback_decision_template_v2_13.csv",
    )
    args = parser.parse_args()

    rows = []
    if args.deployments.exists():
        deployments = pd.read_csv(args.deployments)
        for row in deployments.loc[
            deployments["deployment_state"].astype(str).eq("rollback_consideration")
        ].to_dict(orient="records"):
            rows.append({
                "source_record_type": "deployment",
                "source_record_id": row["deployment_record_id"],
                "implementation_package_id": row.get("implementation_package_id", ""),
                "deployed_commit_sha": row.get("deployed_commit_sha", ""),
            })

    if args.effects.exists():
        effects = pd.read_csv(args.effects)
        for row in effects.loc[
            effects["effect_state"].astype(str).eq("unexpected_behavior_needs_review")
        ].to_dict(orient="records"):
            rows.append({
                "source_record_type": "effect",
                "source_record_id": row["effect_verification_record_id"],
                "implementation_package_id": row.get("implementation_package_id", ""),
                "deployed_commit_sha": row.get("deployed_commit_sha", ""),
            })

    template = pd.DataFrame(rows)
    if template.empty:
        template = pd.DataFrame(columns=[
            "source_record_type",
            "source_record_id",
            "implementation_package_id",
            "deployed_commit_sha",
        ])

    template["decided_at"] = ""
    template["reviewer_role"] = ""
    template["rollback_target_commit_sha"] = ""
    template["rollback_plan_ref"] = ""
    template["rollback_decision"] = ""
    template["decision_rationale"] = ""

    args.output.parent.mkdir(parents=True, exist_ok=True)
    template.to_csv(args.output, index=False, encoding="utf-8")
    print(f"rows={len(template)}")
    print(f"output={args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
