# -*- coding: utf-8 -*-
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import pandas as pd

ROOT=Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0,str(ROOT))

from src.rule_change_proposals_v2_7 import (
    build_rule_change_proposals,
    validate_proposal_registry,
)
from src.rule_change_proposals_report_v2_7 import (
    render_rule_change_proposals_report,
    summarize_rule_change_proposals,
)


def main() -> int:
    parser=argparse.ArgumentParser(description="Gera propostas v2.7 a partir da concordância v2.6.")
    parser.add_argument(
        "--concordance",
        type=Path,
        default=ROOT/"data_candidate"/"human_workflow_concordance_v2_6"/"human_workflow_concordance_v2_6.csv",
    )
    parser.add_argument(
        "--config",
        type=Path,
        default=ROOT/"config"/"rule_change_proposals_v2_7.json",
    )
    parser.add_argument(
        "--out-dir",
        type=Path,
        default=ROOT/"data_candidate"/"rule_change_proposals_v2_7",
    )
    args=parser.parse_args()

    if not args.concordance.exists():
        raise FileNotFoundError(args.concordance)
    if not args.config.exists():
        raise FileNotFoundError(args.config)

    concordance=pd.read_csv(args.concordance,dtype={"codigo_ibge":"string"})
    config=json.loads(args.config.read_text(encoding="utf-8"))

    proposals=build_rule_change_proposals(concordance)
    proposals=validate_proposal_registry(
        proposals,
        allowed_statuses=set(config["proposal_statuses"]),
        allowed_change_types=set(config["change_types"]),
    )
    summary=summarize_rule_change_proposals(proposals)
    report=render_rule_change_proposals_report(proposals)

    args.out_dir.mkdir(parents=True,exist_ok=True)
    csv_path=args.out_dir/"rule_change_proposals_v2_7.csv"
    json_path=args.out_dir/"rule_change_proposals_summary_v2_7.json"
    report_path=args.out_dir/"rule_change_proposals_report_v2_7.md"

    proposals.to_csv(csv_path,index=False,encoding="utf-8")
    json_path.write_text(json.dumps(summary,ensure_ascii=False,indent=2),encoding="utf-8")
    report_path.write_text(report,encoding="utf-8")

    print(json.dumps(summary,ensure_ascii=False,indent=2))
    return 0


if __name__=="__main__":
    raise SystemExit(main())
