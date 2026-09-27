# -*- coding: utf-8 -*-
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.release_deploy_gate_v2_12 import (
    load_release_gate_config,
    validate_release_deploy_gate,
)


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Valida elegibilidade humana para deploy — v2.12."
    )
    parser.add_argument("--input", type=Path, required=True)
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
        "--config",
        type=Path,
        default=ROOT / "config" / "release_deploy_gate_v2_12.json",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=(
            ROOT
            / "data_candidate"
            / "release_deploy_gate_v2_12"
            / "release_deploy_gate_validated_v2_12.csv"
        ),
    )
    args = parser.parse_args()

    for path in (args.input, args.post_merge, args.config):
        if not path.exists():
            raise FileNotFoundError(path)

    records = pd.read_csv(args.input)
    post_merge = pd.read_csv(args.post_merge)
    config = load_release_gate_config(args.config)

    validated = validate_release_deploy_gate(records, post_merge, config)

    args.output.parent.mkdir(parents=True, exist_ok=True)
    validated.to_csv(args.output, index=False, encoding="utf-8")

    summary = {
        "records": int(len(validated)),
        "eligible_for_human_deploy": int(
            (validated["final_release_decision"]
             == "eligible_for_human_deploy").sum()
        ),
        "blocked": int(
            (validated["final_release_decision"] == "blocked").sum()
        ),
        "deferred": int(
            (validated["final_release_decision"] == "defer").sum()
        ),
        "deploy_eligibility_is_not_deploy": True,
        "automatic_tagging_enabled": False,
        "automatic_deploy_enabled": False,
        "automatic_rollback_enabled": False,
        "human_deploy_required": True,
    }
    print(json.dumps(summary, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
