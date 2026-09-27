# -*- coding: utf-8 -*-
from __future__ import annotations

import argparse
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Gera template de decisão humana de deploy v2.12."
    )
    parser.add_argument(
        "--post-merge",
        type=Path,
        default=ROOT / "data_candidate" / "human_merge_v2_11" / "post_merge_validated_v2_11.csv",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=ROOT / "data_candidate" / "deployment_v2_12" / "human_deploy_decision_template_v2_12.csv",
    )
    args = parser.parse_args()

    if not args.post_merge.exists():
        raise FileNotFoundError(args.post_merge)

    post = pd.read_csv(args.post_merge)
    required = {
        "post_merge_record_id",
        "implementation_package_id",
        "merged_commit_sha",
        "post_merge_state",
    }
    missing = required.difference(post.columns)
    if missing:
        raise ValueError(f"Pós-merge v2.11 sem colunas: {sorted(missing)}")

    eligible = post.loc[
        post["post_merge_state"].astype(str).eq("verified_healthy")
    ].copy()

    template = eligible[[
        "post_merge_record_id",
        "implementation_package_id",
        "merged_commit_sha",
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
