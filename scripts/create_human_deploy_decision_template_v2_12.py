# -*- coding: utf-8 -*-
from __future__ import annotations

import argparse
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Gera template de decisão humana de deploy v2.12 a partir do release gate."
    )
    parser.add_argument(
        "--release-gate",
        type=Path,
        default=(
            ROOT
            / "data_candidate"
            / "release_deploy_gate_v2_12"
            / "release_deploy_gate_validated_v2_12.csv"
        ),
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=(
            ROOT
            / "data_candidate"
            / "deployment_v2_12"
            / "human_deploy_decision_template_v2_12.csv"
        ),
    )
    args = parser.parse_args()

    if not args.release_gate.exists():
        raise FileNotFoundError(args.release_gate)

    gate = pd.read_csv(args.release_gate)
    required = {
        "release_gate_record_id",
        "post_merge_record_id",
        "implementation_package_id",
        "release_commit_sha",
        "target_environment",
        "final_release_decision",
    }
    missing = required.difference(gate.columns)
    if missing:
        raise ValueError(f"Release gate v2.12 sem colunas: {sorted(missing)}")

    eligible = gate.loc[
        gate["final_release_decision"]
        .astype(str)
        .eq("eligible_for_human_deploy")
    ].copy()

    template = eligible[[
        "release_gate_record_id",
        "post_merge_record_id",
        "implementation_package_id",
        "release_commit_sha",
        "target_environment",
    ]].copy()
    template["decided_at"] = ""
    template["reviewer_role"] = ""
    template["deploy_decision"] = ""
    template["decision_rationale"] = ""

    args.output.parent.mkdir(parents=True, exist_ok=True)
    template.to_csv(args.output, index=False, encoding="utf-8")
    print(f"rows={len(template)}")
    print(f"output={args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
