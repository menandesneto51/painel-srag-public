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

from src.human_workflow_concordance_v2_6 import (
    build_human_workflow_concordance,
    load_concordance_config,
)
from src.human_workflow_concordance_report_v2_6 import (
    build_concordance_metadata,
    render_concordance_report,
)


def read_optional(path: Path) -> pd.DataFrame | None:
    if not path.exists():
        return None
    return pd.read_csv(path, dtype={"codigo_ibge": "string"})


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Avalia concordância entre regras do workflow e decisões humanas — v2.6."
    )
    parser.add_argument(
        "--decisions",
        type=Path,
        default=ROOT / "data_candidate" / "decision_audit_v2_5" / "human_decisions_validated_v2_5.csv",
    )
    parser.add_argument(
        "--stability",
        type=Path,
        default=ROOT / "data_candidate" / "operational_stability" / "operational_stability_v2_4.csv",
    )
    parser.add_argument(
        "--follow-up-status",
        type=Path,
        default=ROOT / "data_candidate" / "decision_audit_v2_5" / "follow_up_status_v2_5.csv",
    )
    parser.add_argument(
        "--config",
        type=Path,
        default=ROOT / "config" / "human_workflow_concordance_v2_6.json",
    )
    parser.add_argument(
        "--out-dir",
        type=Path,
        default=ROOT / "data_candidate" / "human_workflow_concordance_v2_6",
    )
    args = parser.parse_args()

    if not args.decisions.exists():
        raise FileNotFoundError(args.decisions)
    if not args.config.exists():
        raise FileNotFoundError(args.config)

    decisions = pd.read_csv(
        args.decisions, dtype={"codigo_ibge": "string"}
    )
    stability = read_optional(args.stability)
    follow_up = read_optional(args.follow_up_status)
    config = load_concordance_config(args.config)

    concordance = build_human_workflow_concordance(
        decisions,
        config,
        operational_stability=stability,
        follow_up_status=follow_up,
    )
    metadata = build_concordance_metadata(concordance)
    report = render_concordance_report(concordance)

    args.out_dir.mkdir(parents=True, exist_ok=True)
    csv_path = args.out_dir / "human_workflow_concordance_v2_6.csv"
    json_path = args.out_dir / "human_workflow_concordance_summary_v2_6.json"
    report_path = args.out_dir / "human_workflow_concordance_report_v2_6.md"

    concordance.to_csv(csv_path, index=False, encoding="utf-8")
    json_path.write_text(
        json.dumps(metadata, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    report_path.write_text(report, encoding="utf-8")

    print(json.dumps(metadata, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
