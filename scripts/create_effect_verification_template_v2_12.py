# -*- coding: utf-8 -*-
from __future__ import annotations

import argparse
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Gera template de verificação pós-deploy v2.12."
    )
    parser.add_argument(
        "--deployments",
        type=Path,
        default=ROOT / "data_candidate" / "deployment_v2_12" / "deployment_records_validated_v2_12.csv",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=ROOT / "data_candidate" / "deployment_v2_12" / "effect_verification_template_v2_12.csv",
    )
    args = parser.parse_args()

    if not args.deployments.exists():
        raise FileNotFoundError(args.deployments)

    deployments = pd.read_csv(args.deployments)
    template = deployments[[
        "deployment_record_id",
        "implementation_package_id",
        "deployed_commit_sha",
    ]].copy()

    for col in (
        "measured_at",
        "reviewer_role",
        "observation_window_start",
        "observation_window_end",
        "effect_state",
        "expected_behavior_summary",
        "observed_behavior_summary",
        "evidence_refs",
        "effect_review_notes",
    ):
        template[col] = ""

    args.output.parent.mkdir(parents=True, exist_ok=True)
    template.to_csv(args.output, index=False, encoding="utf-8")
    print(f"rows={len(template)}")
    print(f"output={args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
