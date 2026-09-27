# -*- coding: utf-8 -*-
from __future__ import annotations

import argparse
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Gera template do gate de merge v2.10 para pacotes v2.9 prontos."
    )
    parser.add_argument(
        "--packages",
        type=Path,
        default=ROOT / "data_candidate" / "implementation_package_v2_9" / "implementation_packages_validated_v2_9.csv",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=ROOT / "data_candidate" / "merge_gate_v2_10" / "merge_gate_template_v2_10.csv",
    )
    args = parser.parse_args()

    if not args.packages.exists():
        raise FileNotFoundError(args.packages)

    packages = pd.read_csv(args.packages)
    required = {
        "implementation_package_id",
        "proposal_id",
        "evaluation_record_id",
        "proposal_type",
        "package_status",
        "source_branch",
        "source_commit_sha",
        "target_paths",
        "target_branch_suggestion",
    }
    missing = required.difference(packages.columns)
    if missing:
        raise ValueError(f"Pacotes v2.9 sem colunas: {sorted(missing)}")

    ready = packages.loc[
        packages["package_status"].astype(str).eq("ready_for_manual_branch")
    ].copy()

    if ready.empty:
        template = pd.DataFrame(columns=[
            "implementation_package_id",
            "proposal_id",
            "evaluation_record_id",
            "proposal_type",
            "target_branch_suggestion",
            "authorized_target_paths",
            "evaluated_at",
            "reviewer_role",
            "implementation_branch",
            "source_commit_sha",
            "implementation_commit_sha",
            "changed_paths",
            "diff_review_status",
            "scope_review_status",
            "ci_status",
            "regression_tests_status",
            "backtest_status",
            "epidemiology_revalidation_status",
            "statistical_revalidation_status",
            "security_privacy_review_status",
            "acceptance_criteria_status",
            "rollback_verification_status",
            "final_gate_decision",
            "gate_rationale",
        ])
    else:
        template = ready[[
            "implementation_package_id",
            "proposal_id",
            "evaluation_record_id",
            "proposal_type",
            "target_branch_suggestion",
            "target_paths",
            "source_commit_sha",
        ]].copy()
        template = template.rename(
            columns={"target_paths": "authorized_target_paths"}
        )
        template["evaluated_at"] = ""
        template["reviewer_role"] = ""
        template["implementation_branch"] = template[
            "target_branch_suggestion"
        ]
        template["implementation_commit_sha"] = ""
        template["changed_paths"] = ""

        for col in (
            "diff_review_status",
            "scope_review_status",
            "ci_status",
            "regression_tests_status",
            "backtest_status",
            "epidemiology_revalidation_status",
            "statistical_revalidation_status",
            "security_privacy_review_status",
            "acceptance_criteria_status",
            "rollback_verification_status",
            "final_gate_decision",
            "gate_rationale",
        ):
            template[col] = ""

    args.output.parent.mkdir(parents=True, exist_ok=True)
    template.to_csv(args.output, index=False, encoding="utf-8")
    print(f"rows={len(template)}")
    print(f"output={args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
