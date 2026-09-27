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

from src.rule_shadow_evaluation_v2_7 import compare_shadow_assignments
from src.rule_shadow_evaluation_report_v2_7 import (
    build_shadow_metadata,
    render_shadow_report,
)


def read_optional(path: Path) -> pd.DataFrame | None:
    if not path.exists():
        return None
    return pd.read_csv(path, dtype={"codigo_ibge": "string"})


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Avalia regra candidata em modo sombra — SRAG MT v2.7."
    )
    parser.add_argument("--proposal-id", required=True)
    parser.add_argument("--candidate-queue", type=Path, required=True)
    parser.add_argument("--candidate-rule-version", required=True)
    parser.add_argument(
        "--current-rule-version",
        default="v2.2-current",
    )
    parser.add_argument(
        "--current-queue",
        type=Path,
        default=ROOT / "data_candidate" / "operational_v2_2" / "municipal_review_queue_v2_2.csv",
    )
    parser.add_argument(
        "--proposal-registry",
        type=Path,
        default=ROOT / "data_candidate" / "rule_change_proposals_v2_7" / "rule_change_proposals_v2_7.csv",
    )
    parser.add_argument(
        "--decisions",
        type=Path,
        default=ROOT / "data_candidate" / "decision_audit_v2_5" / "human_decisions_validated_v2_5.csv",
    )
    parser.add_argument(
        "--concordance-config",
        type=Path,
        default=ROOT / "config" / "human_workflow_concordance_v2_6.json",
    )
    parser.add_argument(
        "--shadow-config",
        type=Path,
        default=ROOT / "config" / "rule_shadow_evaluation_v2_7.json",
    )
    parser.add_argument(
        "--out-root",
        type=Path,
        default=ROOT / "data_candidate" / "rule_shadow_evaluation_v2_7",
    )
    args = parser.parse_args()

    for path in (
        args.current_queue,
        args.candidate_queue,
        args.proposal_registry,
        args.concordance_config,
        args.shadow_config,
    ):
        if not path.exists():
            raise FileNotFoundError(path)

    registry = pd.read_csv(args.proposal_registry)
    matches = registry.loc[
        registry["proposal_id"].astype(str).eq(args.proposal_id)
    ]
    if len(matches) != 1:
        raise ValueError(
            f"proposal_id deve existir uma única vez no registro: {args.proposal_id}"
        )
    proposal_status = str(matches.iloc[0]["proposal_status"])

    shadow_cfg = json.loads(
        args.shadow_config.read_text(encoding="utf-8")
    )
    allowed_statuses = set(
        shadow_cfg["allowed_proposal_statuses_for_shadow"]
    )
    if proposal_status not in allowed_statuses:
        raise ValueError(
            f"Proposta em status não elegível para shadow: {proposal_status}"
        )

    concordance_cfg = json.loads(
        args.concordance_config.read_text(encoding="utf-8")
    )

    current = pd.read_csv(
        args.current_queue, dtype={"codigo_ibge": "string"}
    )
    candidate = pd.read_csv(
        args.candidate_queue, dtype={"codigo_ibge": "string"}
    )
    decisions = read_optional(args.decisions)

    shadow = compare_shadow_assignments(
        current,
        candidate,
        required_municipalities=int(
            shadow_cfg["required_municipalities"]
        ),
        decisions=decisions,
        routine_queue=concordance_cfg["routine_queue"],
        escalation_decisions=set(
            concordance_cfg["escalation_decisions"]
        ),
        non_escalation_decisions=set(
            concordance_cfg["non_escalation_decisions"]
        ),
        proposal_id=args.proposal_id,
        candidate_rule_version=args.candidate_rule_version,
    )

    metadata = build_shadow_metadata(
        shadow,
        proposal_id=args.proposal_id,
        proposal_status=proposal_status,
        current_rule_version=args.current_rule_version,
        candidate_rule_version=args.candidate_rule_version,
    )
    report = render_shadow_report(
        shadow,
        proposal_id=args.proposal_id,
        proposal_status=proposal_status,
        current_rule_version=args.current_rule_version,
        candidate_rule_version=args.candidate_rule_version,
    )

    out_dir = args.out_root / args.proposal_id
    out_dir.mkdir(parents=True, exist_ok=True)
    csv_path = out_dir / "rule_shadow_evaluation_v2_7.csv"
    meta_path = out_dir / "rule_shadow_evaluation_summary_v2_7.json"
    report_path = out_dir / "rule_shadow_evaluation_report_v2_7.md"

    shadow.to_csv(csv_path, index=False, encoding="utf-8")
    meta_path.write_text(
        json.dumps(metadata, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    report_path.write_text(report, encoding="utf-8")

    print(json.dumps(metadata, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
