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

from src.deployment_verification_report_v2_12 import (
    build_deployment_verification_summary,
    render_deployment_verification_markdown,
)


def read_optional(path: Path) -> pd.DataFrame | None:
    if not path.exists():
        return None
    return pd.read_csv(path)


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Gera relatório estadual de deploy e efeito v2.12."
    )
    parser.add_argument(
        "--decisions",
        type=Path,
        default=ROOT / "data_candidate" / "deployment_v2_12" / "human_deploy_decisions_validated_v2_12.csv",
    )
    parser.add_argument(
        "--deployments",
        type=Path,
        default=ROOT / "data_candidate" / "deployment_v2_12" / "deployment_records_validated_v2_12.csv",
    )
    parser.add_argument(
        "--effects",
        type=Path,
        default=ROOT / "data_candidate" / "deployment_v2_12" / "effect_verification_validated_v2_12.csv",
    )
    parser.add_argument(
        "--out-dir",
        type=Path,
        default=ROOT / "data_candidate" / "deployment_v2_12",
    )
    args = parser.parse_args()

    decisions = read_optional(args.decisions)
    deployments = read_optional(args.deployments)
    effects = read_optional(args.effects)

    summary = build_deployment_verification_summary(
        decisions, deployments, effects
    )
    report = render_deployment_verification_markdown(summary)

    args.out_dir.mkdir(parents=True, exist_ok=True)
    (args.out_dir / "deployment_verification_summary_v2_12.json").write_text(
        json.dumps(summary, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    (args.out_dir / "deployment_verification_report_v2_12.md").write_text(
        report,
        encoding="utf-8",
    )

    print(json.dumps(summary, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
