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

from src.implementation_package_report_v2_9 import (
    render_implementation_package_report,
    summarize_implementation_packages,
)


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Gera relatório dos pacotes de implementação v2.9."
    )
    parser.add_argument(
        "--packages",
        type=Path,
        default=ROOT / "data_candidate" / "implementation_package_v2_9" / "implementation_packages_validated_v2_9.csv",
    )
    parser.add_argument(
        "--out-dir",
        type=Path,
        default=ROOT / "data_candidate" / "implementation_package_v2_9",
    )
    args = parser.parse_args()

    if not args.packages.exists():
        raise FileNotFoundError(args.packages)

    packages = pd.read_csv(args.packages)
    summary = summarize_implementation_packages(packages)
    report = render_implementation_package_report(packages)

    args.out_dir.mkdir(parents=True, exist_ok=True)
    (args.out_dir / "implementation_package_summary_v2_9.json").write_text(
        json.dumps(summary, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    (args.out_dir / "implementation_package_report_v2_9.md").write_text(
        report,
        encoding="utf-8",
    )

    print(json.dumps(summary, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
