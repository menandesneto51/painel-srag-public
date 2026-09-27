# -*- coding: utf-8 -*-
from __future__ import annotations

import argparse
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Gera template de post-mortem v2.14 a partir de efeito v2.12 e rollback v2.13."
    )
    parser.add_argument(
        "--effects",
        type=Path,
        default=ROOT / "data_candidate" / "deployment_v2_12" / "effect_verification_validated_v2_12.csv",
    )
    parser.add_argument(
        "--rollbacks",
        type=Path,
        default=ROOT / "data_candidate" / "rollback_v2_13" / "rollback_execution_validated_v2_13.csv",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=ROOT / "data_candidate" / "postmortem_v2_14" / "postmortem_template_v2_14.csv",
    )
    args = parser.parse_args()

    rows = []

    if args.effects.exists():
        effects = pd.read_csv(args.effects)
        required = {
            "effect_verification_record_id",
            "implementation_package_id",
            "deployed_commit_sha",
            "effect_state",
        }
        missing = required.difference(effects.columns)
        if missing:
            raise ValueError(f"Efeitos v2.12 sem colunas: {sorted(missing)}")

        for row in effects.to_dict(orient="records"):
            rows.append({
                "source_record_type": "effect",
                "source_record_id": row["effect_verification_record_id"],
                "implementation_package_id": row["implementation_package_id"],
                "technical_commit_sha": row["deployed_commit_sha"],
                "source_state": row["effect_state"],
            })

    if args.rollbacks.exists():
        rollbacks = pd.read_csv(args.rollbacks)
        required = {
            "rollback_execution_record_id",
            "implementation_package_id",
            "rolled_back_commit_sha",
            "rollback_execution_state",
        }
        missing = required.difference(rollbacks.columns)
        if missing:
            raise ValueError(f"Rollback v2.13 sem colunas: {sorted(missing)}")

        for row in rollbacks.to_dict(orient="records"):
            rows.append({
                "source_record_type": "rollback",
                "source_record_id": row["rollback_execution_record_id"],
                "implementation_package_id": row["implementation_package_id"],
                "technical_commit_sha": row["rolled_back_commit_sha"],
                "source_state": row["rollback_execution_state"],
            })

    template = pd.DataFrame(rows)
    if template.empty:
        template = pd.DataFrame(columns=[
            "source_record_type",
            "source_record_id",
            "implementation_package_id",
            "technical_commit_sha",
            "source_state",
        ])

    for col in (
        "conducted_at",
        "reviewer_role",
        "postmortem_status",
        "outcome_state",
        "event_summary",
        "expected_behavior_summary",
        "observed_behavior_summary",
        "contributing_factors",
        "safeguards_that_worked",
        "safeguards_to_improve",
        "lessons_learned",
        "learning_action_type",
        "follow_up_actions",
        "evidence_refs",
        "reenter_rule_review",
        "rule_review_scope",
        "rule_review_reason",
    ):
        template[col] = ""

    args.output.parent.mkdir(parents=True, exist_ok=True)
    template.to_csv(args.output, index=False, encoding="utf-8")
    print(f"rows={len(template)}")
    print(f"output={args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
