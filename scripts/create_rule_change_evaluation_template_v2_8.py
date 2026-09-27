# -*- coding: utf-8 -*-
from __future__ import annotations

import argparse
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Gera template de avaliação formal das propostas v2.7."
    )
    parser.add_argument(
        "--proposals",
        type=Path,
        default=ROOT / "data_candidate" / "rule_change_proposals_v2_7" / "rule_change_proposals_v2_7.csv",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=ROOT / "data_candidate" / "rule_change_evaluation_v2_8" / "rule_change_evaluation_template_v2_8.csv",
    )
    args = parser.parse_args()

    if not args.proposals.exists():
        raise FileNotFoundError(args.proposals)

    proposals = pd.read_csv(args.proposals)
    required = {
        "proposal_id",
        "proposal_type",
        "proposal_status",
        "rule_key",
        "problem_statement",
        "analysis_required",
    }
    missing = required.difference(proposals.columns)
    if missing:
        raise ValueError(f"Propostas v2.7 sem colunas: {sorted(missing)}")

    template = proposals[[
        "proposal_id",
        "proposal_type",
        "proposal_status",
        "rule_key",
        "problem_statement",
        "analysis_required",
    ]].copy()

    for col in (
        "evaluated_at",
        "reviewer_role",
        "case_review_status",
        "case_review_refs",
        "epidemiology_review_status",
        "epidemiology_review_refs",
        "shadow_review_status",
        "shadow_review_refs",
        "backtest_status",
        "backtest_refs",
        "statistical_review_status",
        "statistical_review_refs",
        "documentation_status",
        "documentation_refs",
        "impact_summary",
        "risk_summary",
        "final_decision",
        "decision_rationale",
        "implementation_notes",
    ):
        template[col] = ""

    args.output.parent.mkdir(parents=True, exist_ok=True)
    template.to_csv(args.output, index=False, encoding="utf-8")
    print(f"rows={len(template)}")
    print(f"output={args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
