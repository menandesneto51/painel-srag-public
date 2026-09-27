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

from src.operational_stability import (
    analyze_operational_stability,
    render_operational_stability_report,
    summarize_operational_stability,
)


def load_vintages(root: Path) -> list[tuple[str, pd.DataFrame]]:
    if not root.exists():
        raise FileNotFoundError(root)

    items = []
    for directory in sorted(p for p in root.iterdir() if p.is_dir()):
        queue = directory / "municipal_review_queue_v2_2.csv"
        meta = directory / "metadata.json"
        if not queue.exists():
            continue

        snapshot_id = directory.name
        if meta.exists():
            payload = json.loads(meta.read_text(encoding="utf-8"))
            snapshot_id = str(payload.get("snapshot_id") or snapshot_id)

        frame = pd.read_csv(
            queue,
            dtype={"codigo_ibge": "string"},
        )
        items.append((snapshot_id, frame))

    if not items:
        raise ValueError("Nenhum vintage operacional encontrado.")
    return items


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Analisa estabilidade de workflow em múltiplos vintages v2.2."
    )
    parser.add_argument(
        "--vintages-root",
        type=Path,
        default=ROOT / "data_candidate" / "operational_vintages",
    )
    parser.add_argument(
        "--config",
        type=Path,
        default=ROOT / "config" / "operational_stability_v2_4.json",
    )
    parser.add_argument(
        "--out-dir",
        type=Path,
        default=ROOT / "data_candidate" / "operational_stability",
    )
    args = parser.parse_args()

    cfg = json.loads(args.config.read_text(encoding="utf-8"))
    vintages = load_vintages(args.vintages_root)

    stability = analyze_operational_stability(
        vintages,
        routine_queue=cfg["routine_queue"],
        window_vintages=int(cfg["window_vintages"]),
        persistence_threshold_cycles=int(
            cfg["persistence_threshold_cycles"]
        ),
        sustained_threshold_cycles=int(
            cfg["sustained_threshold_cycles"]
        ),
    )
    summary = summarize_operational_stability(stability)
    report = render_operational_stability_report(stability)

    args.out_dir.mkdir(parents=True, exist_ok=True)
    stability.to_csv(
        args.out_dir / "operational_stability_v2_4.csv",
        index=False,
        encoding="utf-8",
    )
    summary.to_csv(
        args.out_dir / "operational_stability_summary_v2_4.csv",
        index=False,
        encoding="utf-8",
    )
    (args.out_dir / "operational_stability_report_v2_4.md").write_text(
        report,
        encoding="utf-8",
    )

    print(f"vintages_found={len(vintages)}")
    print(f"vintages_used={min(len(vintages), int(cfg['window_vintages']))}")
    print(summary.to_string(index=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
