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

from src.governance_observability_v2_16 import (
    build_proposal_governance_status,
    build_transition_metrics,
    load_governance_observability_config,
)
from src.governance_observability_report_v2_16 import (
    build_governance_observability_metadata,
    render_governance_observability_report,
)


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Gera observabilidade do processo de governança v2.16."
    )
    parser.add_argument(
        "--ledger",
        type=Path,
        default=(
            ROOT
            / "data_candidate"
            / "change_lifecycle_v2_15"
            / "change_lifecycle_ledger_v2_15.csv"
        ),
    )
    parser.add_argument(
        "--config",
        type=Path,
        default=ROOT / "config" / "governance_observability_v2_16.json",
    )
    parser.add_argument(
        "--as-of",
        required=True,
        help="Data/hora ISO 8601 com timezone para cálculo reprodutível.",
    )
    parser.add_argument(
        "--out-dir",
        type=Path,
        default=ROOT / "data_candidate" / "governance_observability_v2_16",
    )
    args = parser.parse_args()

    if not args.ledger.exists():
        raise FileNotFoundError(args.ledger)
    if not args.config.exists():
        raise FileNotFoundError(args.config)

    ledger = pd.read_csv(args.ledger)
    config = load_governance_observability_config(args.config)

    transitions = build_transition_metrics(ledger)
    proposal_status = build_proposal_governance_status(
        ledger,
        config,
        as_of=args.as_of,
    )
    metadata = build_governance_observability_metadata(
        proposal_status,
        transitions,
    )
    report = render_governance_observability_report(
        proposal_status,
        transitions,
    )

    args.out_dir.mkdir(parents=True, exist_ok=True)
    transitions.to_csv(
        args.out_dir / "governance_transition_metrics_v2_16.csv",
        index=False,
        encoding="utf-8",
    )
    proposal_status.to_csv(
        args.out_dir / "governance_proposal_status_v2_16.csv",
        index=False,
        encoding="utf-8",
    )
    (args.out_dir / "governance_observability_summary_v2_16.json").write_text(
        json.dumps(metadata, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    (args.out_dir / "governance_observability_report_v2_16.md").write_text(
        report,
        encoding="utf-8",
    )

    print(json.dumps(metadata, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
