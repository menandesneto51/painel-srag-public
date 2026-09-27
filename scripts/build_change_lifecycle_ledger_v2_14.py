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

from src.change_lifecycle_ledger_v2_14 import (
    build_change_lifecycle_ledger,
    load_ledger_config,
)
from src.change_lifecycle_report_v2_14 import (
    build_change_lifecycle_metadata,
    render_change_lifecycle_report,
)


def read_optional(path: Path) -> pd.DataFrame | None:
    if not path.exists():
        return None
    return pd.read_csv(path)


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Constrói o ledger auditável do ciclo de mudança v2.14."
    )
    parser.add_argument(
        "--proposals",
        type=Path,
        default=(
            ROOT
            / "data_candidate"
            / "rule_change_proposals_v2_7"
            / "rule_change_proposals_v2_7.csv"
        ),
    )
    parser.add_argument(
        "--evaluations",
        type=Path,
        default=(
            ROOT
            / "data_candidate"
            / "rule_change_evaluation_v2_8"
            / "rule_change_evaluations_validated_v2_8.csv"
        ),
    )
    parser.add_argument(
        "--packages",
        type=Path,
        default=(
            ROOT
            / "data_candidate"
            / "implementation_package_v2_9"
            / "implementation_packages_validated_v2_9.csv"
        ),
    )
    parser.add_argument(
        "--merge-gates",
        type=Path,
        default=(
            ROOT
            / "data_candidate"
            / "merge_gate_v2_10"
            / "merge_gate_validated_v2_10.csv"
        ),
    )
    parser.add_argument(
        "--merge-decisions",
        type=Path,
        default=(
            ROOT
            / "data_candidate"
            / "human_merge_v2_11"
            / "human_merge_decisions_validated_v2_11.csv"
        ),
    )
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
        "--release-gates",
        type=Path,
        default=(
            ROOT
            / "data_candidate"
            / "release_deploy_gate_v2_12"
            / "release_deploy_gate_validated_v2_12.csv"
        ),
    )
    parser.add_argument(
        "--deploy-decisions",
        type=Path,
        default=(
            ROOT
            / "data_candidate"
            / "deployment_v2_12"
            / "human_deploy_decisions_validated_v2_12.csv"
        ),
    )
    parser.add_argument(
        "--deployments",
        type=Path,
        default=(
            ROOT
            / "data_candidate"
            / "deployment_v2_12"
            / "deployment_records_validated_v2_12.csv"
        ),
    )
    parser.add_argument(
        "--effects",
        type=Path,
        default=(
            ROOT
            / "data_candidate"
            / "deployment_v2_12"
            / "effect_verification_validated_v2_12.csv"
        ),
    )
    parser.add_argument(
        "--rollback-decisions",
        type=Path,
        default=(
            ROOT
            / "data_candidate"
            / "rollback_v2_13"
            / "human_rollback_decisions_validated_v2_13.csv"
        ),
    )
    parser.add_argument(
        "--rollback-executions",
        type=Path,
        default=(
            ROOT
            / "data_candidate"
            / "rollback_v2_13"
            / "rollback_execution_validated_v2_13.csv"
        ),
    )
    parser.add_argument(
        "--config",
        type=Path,
        default=ROOT / "config" / "change_lifecycle_ledger_v2_14.json",
    )
    parser.add_argument(
        "--out-dir",
        type=Path,
        default=ROOT / "data_candidate" / "change_lifecycle_v2_14",
    )
    args = parser.parse_args()

    if not args.proposals.exists():
        raise FileNotFoundError(args.proposals)
    if not args.config.exists():
        raise FileNotFoundError(args.config)

    config = load_ledger_config(args.config)
    ledger = build_change_lifecycle_ledger(
        proposals=pd.read_csv(args.proposals),
        evaluations=read_optional(args.evaluations),
        packages=read_optional(args.packages),
        merge_gates=read_optional(args.merge_gates),
        merge_decisions=read_optional(args.merge_decisions),
        post_merge=read_optional(args.post_merge),
        release_gates=read_optional(args.release_gates),
        deploy_decisions=read_optional(args.deploy_decisions),
        deployments=read_optional(args.deployments),
        effects=read_optional(args.effects),
        rollback_decisions=read_optional(args.rollback_decisions),
        rollback_executions=read_optional(args.rollback_executions),
        config=config,
    )

    metadata = build_change_lifecycle_metadata(ledger)
    report = render_change_lifecycle_report(ledger)

    args.out_dir.mkdir(parents=True, exist_ok=True)
    ledger.to_csv(
        args.out_dir / "change_lifecycle_ledger_v2_14.csv",
        index=False,
        encoding="utf-8",
    )
    (args.out_dir / "change_lifecycle_summary_v2_14.json").write_text(
        json.dumps(metadata, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    (args.out_dir / "change_lifecycle_report_v2_14.md").write_text(
        report,
        encoding="utf-8",
    )

    print(json.dumps(metadata, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
