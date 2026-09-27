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

from src.candidate_rule_queue_v2_7 import build_candidate_review_queue


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Gera fila candidata v2.7 isolada da configuração vigente."
    )
    parser.add_argument("--proposal-id", required=True)
    parser.add_argument("--candidate-rule-version", required=True)
    parser.add_argument("--candidate-config", type=Path, required=True)
    parser.add_argument(
        "--review-cards",
        type=Path,
        default=(
            ROOT
            / "data_candidate"
            / "territorial_intelligence"
            / "territorial_review_cards_v2_1.csv"
        ),
    )
    parser.add_argument(
        "--proposal-registry",
        type=Path,
        default=(
            ROOT
            / "data_candidate"
            / "rule_change_proposals_v2_7"
            / "rule_change_proposals_v2_7.csv"
        ),
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
        args.candidate_config,
        args.review_cards,
        args.proposal_registry,
        args.shadow_config,
    ):
        if not path.exists():
            raise FileNotFoundError(path)

    registry = pd.read_csv(args.proposal_registry)
    match = registry.loc[
        registry["proposal_id"].astype(str).eq(args.proposal_id)
    ]
    if len(match) != 1:
        raise ValueError(
            f"proposal_id deve existir uma única vez: {args.proposal_id}"
        )

    shadow_cfg = json.loads(
        args.shadow_config.read_text(encoding="utf-8")
    )
    allowed = set(
        shadow_cfg["allowed_proposal_statuses_for_shadow"]
    )
    status = str(match.iloc[0]["proposal_status"])
    if status not in allowed:
        raise ValueError(
            f"Proposta não elegível para shadow no status atual: {status}"
        )

    candidate_cfg = json.loads(
        args.candidate_config.read_text(encoding="utf-8")
    )
    cards = pd.read_csv(
        args.review_cards,
        dtype={"codigo_ibge": "string"},
    )

    queue = build_candidate_review_queue(
        cards,
        candidate_cfg,
        proposal_id=args.proposal_id,
        candidate_rule_version=args.candidate_rule_version,
        required_municipalities=int(
            shadow_cfg["required_municipalities"]
        ),
    )

    out_dir = args.out_root / args.proposal_id
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / "candidate_review_queue_v2_7.csv"
    queue.to_csv(out_path, index=False, encoding="utf-8")

    metadata = {
        "proposal_id": args.proposal_id,
        "proposal_status": status,
        "candidate_rule_version": args.candidate_rule_version,
        "municipalities": int(queue["codigo_ibge"].nunique()),
        "candidate_only": True,
        "shadow_only": True,
        "automatic_activation_enabled": False,
        "automatic_rule_change_enabled": False,
    }
    (out_dir / "candidate_review_queue_v2_7.metadata.json").write_text(
        json.dumps(metadata, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

    print(json.dumps(metadata, ensure_ascii=False, indent=2))
    print(f"output={out_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
