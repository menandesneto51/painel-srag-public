# -*- coding: utf-8 -*-
from __future__ import annotations

import argparse
import json
import shutil
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Captura um vintage agregado da fila operacional v2.2."
    )
    parser.add_argument(
        "--queue",
        type=Path,
        default=ROOT / "data_candidate" / "operational_v2_2" / "municipal_review_queue_v2_2.csv",
    )
    parser.add_argument(
        "--out-root",
        type=Path,
        default=ROOT / "data_candidate" / "operational_vintages",
    )
    parser.add_argument("--snapshot-id", default=None)
    args = parser.parse_args()

    if not args.queue.exists():
        raise FileNotFoundError(args.queue)

    queue = pd.read_csv(args.queue, dtype={"codigo_ibge": "string"})
    if len(queue) != 142 or queue["codigo_ibge"].nunique() != 142:
        raise ValueError("Fila capturada deve conter 142 municípios.")

    snapshot_id = args.snapshot_id or datetime.now(timezone.utc).strftime(
        "%Y%m%dT%H%M%SZ"
    )
    out_dir = args.out_root / snapshot_id
    if out_dir.exists():
        raise FileExistsError(f"Vintage já existe: {out_dir}")
    out_dir.mkdir(parents=True)

    shutil.copy2(args.queue, out_dir / "municipal_review_queue_v2_2.csv")
    metadata = {
        "snapshot_id": snapshot_id,
        "captured_at": datetime.now(timezone.utc).isoformat(),
        "rows": int(len(queue)),
        "municipalities": int(queue["codigo_ibge"].nunique()),
        "aggregate_only": True,
        "queue_is_not_risk_rank": True,
        "automatic_action_enabled": False,
    }
    (out_dir / "metadata.json").write_text(
        json.dumps(metadata, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    print(json.dumps(metadata, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
