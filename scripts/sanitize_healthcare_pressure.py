# -*- coding: utf-8 -*-
from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.healthcare_pressure_bridge import sanitize_healthcare_pressure


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Sanitiza export agregado de pressão assistencial para uso na v2.1/v2.2."
    )
    parser.add_argument("--input", type=Path, required=True)
    parser.add_argument("--stable-week", type=int, required=True)
    parser.add_argument(
        "--output",
        type=Path,
        default=ROOT / "data_candidate" / "healthcare_pressure_sanitized.csv",
    )
    args = parser.parse_args()

    if not args.input.exists():
        raise FileNotFoundError(args.input)

    frame = pd.read_csv(args.input, dtype={"codigo_ibge": "string"})
    sanitized = sanitize_healthcare_pressure(
        frame,
        stable_week=args.stable_week,
    )

    args.output.parent.mkdir(parents=True, exist_ok=True)
    sanitized.to_csv(args.output, index=False, encoding="utf-8")

    meta = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "rows": int(len(sanitized)),
        "stable_week": int(args.stable_week),
        "sanitization_status": "aggregate_contract_passed",
        "patient_level_fields_present": False,
        "automatic_pressure_classification_enabled": False,
    }
    meta_path = args.output.with_suffix(".metadata.json")
    meta_path.write_text(
        json.dumps(meta, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    print(json.dumps(meta, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
