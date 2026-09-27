# -*- coding: utf-8 -*-
from __future__ import annotations

import argparse
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Gera template de decisão humana de merge v2.11."
    )
    parser.add_argument(
        "--gate",
        type=Path,
        default=ROOT / "data_candidate" / "merge_gate_v2_10" / "merge_gate_validated_v2_10.csv",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=ROOT / "data_candidate" / "human_merge_v2_11" / "human_merge_decision_template_v2_11.csv",
    )
    args = parser.parse_args()

    if not args.gate.exists():
        raise FileNotFoundError(args.gate)

    gate = pd.read_csv(args.gate)
    required = {
        "merge_gate_record_id",
        "implementation_package_id",
        "proposal_id",
        "implementation_branch",
        "implementation_commit_sha",
        "final_gate_decision",
    }
    missing = required.difference(gate.columns)
    if missing:
        raise ValueError(f"Gate v2.10 sem colunas: {sorted(missing)}")

    eligible = gate.loc[
        gate["final_gate_decision"]
        .astype(str)
        .eq("eligible_for_human_merge")
    ].copy()

    template = eligible[[
        "merge_gate_record_id",
        "implementation_package_id",
        "proposal_id",
        "implementation_branch",
        "implementation_commit_sha",
    ]].copy()
    template["decided_at"] = ""
    template["reviewer_role"] = ""
    template["merge_decision"] = ""
    template["decision_rationale"] = ""

    args.output.parent.mkdir(parents=True, exist_ok=True)
    template.to_csv(args.output, index=False, encoding="utf-8")
    print(f"rows={len(template)}")
    print(f"output={args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
