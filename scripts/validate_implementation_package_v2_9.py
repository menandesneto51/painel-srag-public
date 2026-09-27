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

from src.implementation_package_v2_9 import (
    load_implementation_package_config,
    validate_implementation_packages,
)


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Valida pacotes de implementação v2.9 sem criar branches ou alterar código."
    )
    parser.add_argument("--input", type=Path, required=True)
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
        "--config",
        type=Path,
        default=ROOT / "config" / "implementation_package_v2_9.json",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=ROOT / "data_candidate" / "implementation_package_v2_9" / "implementation_packages_validated_v2_9.csv",
    )
    args = parser.parse_args()

    for path in (args.input, args.evaluations, args.proposals, args.config):
        if not path.exists():
            raise FileNotFoundError(path)

    packages = pd.read_csv(args.input)
    evaluations = pd.read_csv(args.evaluations)
    proposals = pd.read_csv(args.proposals)
    config = load_implementation_package_config(args.config)

    validated = validate_implementation_packages(
        packages,
        evaluations,
        proposals,
        config,
    )
    args.output.parent.mkdir(parents=True, exist_ok=True)
    validated.to_csv(args.output, index=False, encoding="utf-8")

    summary = {
        "packages": int(len(validated)),
        "ready_for_manual_branch": int(
            (validated["package_status"] == "ready_for_manual_branch").sum()
        ),
        "manual_branch_required": True,
        "automatic_branch_creation_enabled": False,
        "automatic_code_edit_enabled": False,
        "automatic_commit_enabled": False,
        "automatic_merge_enabled": False,
        "automatic_deploy_enabled": False,
    }
    print(json.dumps(summary, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
