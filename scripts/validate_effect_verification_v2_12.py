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
    validate_effect_verification_records,
)


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Valida verificação de efeito pós-deploy v2.12."
    )
    parser.add_argument("--input", type=Path, required=True)
    parser.add_argument(
        "--deployments",
        type=Path,
        default=ROOT / "data_candidate" / "deployment_v2_12" / "deployment_records_validated_v2_12.csv",
    )
    parser.add_argument(
        "--config",
        type=Path,
        default=ROOT / "config" / "deployment_verification_v2_12.json",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=ROOT / "data_candidate" / "deployment_v2_12" / "effect_verification_validated_v2_12.csv",
    )
    args = parser.parse_args()

    for path in (args.input, args.deployments, args.config):
        if not path.exists():
            raise FileNotFoundError(path)

    records = pd.read_csv(args.input)
    deployments = pd.read_csv(args.deployments)
    cfg = load_deployment_config(args.config)

    out = validate_effect_verification_records(
        records,
        deployments,
        cfg,
    )

    args.output.parent.mkdir(parents=True, exist_ok=True)
    out.to_csv(args.output, index=False, encoding="utf-8")

    summary = {
        "records": int(len(out)),
        "effect_verification_is_not_causal_inference": True,
        "automatic_rule_change_enabled": False,
        "automatic_rollback_enabled": False,
    }
    print(json.dumps(summary, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
