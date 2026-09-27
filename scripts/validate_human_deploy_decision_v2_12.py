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

from src.deployment_verification_v2_12 import (
    load_deployment_config,
    validate_human_deploy_decisions,
)


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Valida decisões humanas de deploy v2.12."
    )
    parser.add_argument("--input", type=Path, required=True)
    parser.add_argument(
        "--post-merge",
        type=Path,
        default=ROOT / "data_candidate" / "human_merge_v2_11" / "post_merge_validated_v2_11.csv",
    )
    parser.add_argument(
        "--config",
        type=Path,
        default=ROOT / "config" / "deployment_verification_v2_12.json",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=ROOT / "data_candidate" / "deployment_v2_12" / "human_deploy_decisions_validated_v2_12.csv",
    )
    args = parser.parse_args()

    for path in (args.input, args.post_merge, args.config):
        if not path.exists():
            raise FileNotFoundError(path)

    decisions = pd.read_csv(args.input)
    post_merge = pd.read_csv(args.post_merge)
    cfg = load_deployment_config(args.config)

    out = validate_human_deploy_decisions(
        decisions,
        post_merge,
        cfg,
    )

    args.output.parent.mkdir(parents=True, exist_ok=True)
    out.to_csv(args.output, index=False, encoding="utf-8")

    summary = {
        "records": int(len(out)),
        "approved": int((out["deploy_decision"] == "approve_human_deploy").sum()),
        "rejected": int((out["deploy_decision"] == "reject_deploy").sum()),
        "deferred": int((out["deploy_decision"] == "defer_deploy").sum()),
        "deploy_decision_is_not_deploy_execution": True,
        "automatic_deploy_enabled": False,
        "automatic_rollback_enabled": False,
    }
    print(json.dumps(summary, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
