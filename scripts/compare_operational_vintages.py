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

from src.operational_persistence import (
    compare_operational_vintages,
    render_operational_change_report,
    summarize_operational_changes,
)


def read_metadata(queue_path: Path) -> dict:
    meta = queue_path.parent / "metadata.json"
    if not meta.exists():
        return {}
    return json.loads(meta.read_text(encoding="utf-8"))


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Compara dois vintages agregados da fila operacional."
    )
    parser.add_argument("--current", type=Path, required=True)
    parser.add_argument("--previous", type=Path, default=None)
    parser.add_argument(
        "--out-dir",
        type=Path,
        default=ROOT / "data_candidate" / "operational_persistence",
    )
    args = parser.parse_args()

    current = pd.read_csv(args.current, dtype={"codigo_ibge": "string"})
    previous = (
        pd.read_csv(args.previous, dtype={"codigo_ibge": "string"})
        if args.previous else None
    )

    cur_meta = read_metadata(args.current)
    prev_meta = read_metadata(args.previous) if args.previous else {}

    changes = compare_operational_vintages(
        current,
        previous,
        current_snapshot_id=cur_meta.get("snapshot_id"),
        previous_snapshot_id=prev_meta.get("snapshot_id"),
    )
    summary = summarize_operational_changes(changes)
    report = render_operational_change_report(changes)

    args.out_dir.mkdir(parents=True, exist_ok=True)
    changes.to_csv(
        args.out_dir / "operational_persistence_v2_3.csv",
        index=False,
        encoding="utf-8",
    )
    summary.to_csv(
        args.out_dir / "operational_persistence_summary_v2_3.csv",
        index=False,
        encoding="utf-8",
    )
    (args.out_dir / "operational_persistence_report_v2_3.md").write_text(
        report,
        encoding="utf-8",
    )
    print(summary.to_string(index=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
