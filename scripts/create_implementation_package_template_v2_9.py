# -*- coding: utf-8 -*-
from __future__ import annotations

import argparse
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Gera template de pacote de implementação v2.9 para avaliações v2.8 aprovadas."
    )
    parser.add_argument(
        "--evaluations",
        type=Path,
        default=ROOT / "data_candidate" / "rule_change_evaluation_v2_8" / "rule_change_evaluations_validated_v2_8.csv",
    )
    parser.add_argument(
        "--proposals",
        type=Path,
        default=ROOT / "data_candidate" / "rule_change_proposals_v2_7" / "rule_change_proposals_v2_7.csv",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=ROOT / "data_candidate" / "implementation_package_v2_9" / "implementation_package_template_v2_9.csv",
    )
    args = parser.parse_args()

    for path in (args.evaluations, args.proposals):
        if not path.exists():
            raise FileNotFoundError(path)

    evaluations = pd.read_csv(args.evaluations)
    proposals = pd.read_csv(args.proposals)

    approved = evaluations.loc[
        evaluations["final_decision"]
        .astype(str)
        .eq("approve_for_implementation_branch")
    ].copy()

    if approved.empty:
        template = pd.DataFrame(columns=[
            "proposal_id",
            "evaluation_record_id",
            "proposal_type",
            "rule_key",
            "created_at",
            "planner_role",
            "implementation_summary",
            "target_paths",
            "required_tests",
            "acceptance_criteria",
            "rollback_plan",
            "evidence_refs",
            "package_status",
        ])
    else:
        proposal_meta = proposals[[
            "proposal_id",
            "proposal_type",
            "rule_key",
        ]].drop_duplicates("proposal_id")

        template = approved[[
            "proposal_id",
            "evaluation_record_id",
        ]].merge(
            proposal_meta,
            on="proposal_id",
            how="left",
            validate="many_to_one",
        )
        template["created_at"] = ""
        template["planner_role"] = ""
        template["implementation_summary"] = ""
        template["target_paths"] = ""
        template["required_tests"] = "unit|regression|backtest"
        template["acceptance_criteria"] = ""
        template["rollback_plan"] = ""
        template["evidence_refs"] = template.apply(
            lambda row: f"{row['proposal_id']}|{row['evaluation_record_id']}",
            axis=1,
        )
        template["package_status"] = "draft"

    args.output.parent.mkdir(parents=True, exist_ok=True)
    template.to_csv(args.output, index=False, encoding="utf-8")
    print(f"rows={len(template)}")
    print(f"output={args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
