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

from src.merge_gate_v2_10 import (
    load_merge_gate_config,
    validate_merge_gate,
)


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Valida elegibilidade humana para merge — v2.10."
    )
    parser.add_argument("--input", type=Path, required=True)
    parser.add_argument(
        "--packages",
        type=Path,
        default=ROOT / "data_candidate" / "implementation_package_v2_9" / "implementation_packages_validated_v2_9.csv",
    )
    parser.add_argument(
        "--config",
        type=Path,
        default=ROOT / "config" / "merge_gate_v2_10.json",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=ROOT / "data_candidate" / "merge_gate_v2_10" / "merge_gate_validated_v2_10.csv",
    )
    args = parser.parse_args()

    for path in (args.input, args.packages, args.config):
        if not path.exists():
            raise FileNotFoundError(path)

    gate_records = pd.read_csv(args.input)
    packages = pd.read_csv(args.packages)
    config = load_merge_gate_config(args.config)

    validated = validate_merge_gate(
        gate_records,
        packages,
        config,
    )

    args.output.parent.mkdir(parents=True, exist_ok=True)
    validated.to_csv(args.output, index=False, encoding="utf-8")

    summary = {
        "records": int(len(validated)),
        "eligible_for_human_merge": int(
            (validated["final_gate_decision"] == "eligible_for_human_merge").sum()
        ),
        "blocked": int(
            (validated["final_gate_decision"] == "blocked").sum()
        ),
        "deferred": int(
            (validated["final_gate_decision"] == "defer").sum()
        ),
        "merge_eligibility_is_not_merge": True,
        "automatic_commit_enabled": False,
        "automatic_merge_enabled": False,
        "automatic_deploy_enabled": False,
        "human_merge_required": True,
    }
    print(json.dumps(summary, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
