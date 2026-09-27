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

from src.territorial_intelligence import build_territorial_intelligence


def read_optional_csv(path: Path | None) -> pd.DataFrame | None:
    if path is None:
        return None
    if not path.exists():
        raise FileNotFoundError(f"Arquivo opcional informado não existe: {path}")
    return pd.read_csv(path, dtype={"codigo_ibge": "string"})


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Constrói a camada multidimensional de inteligência territorial SRAG v2.1."
    )
    parser.add_argument(
        "--signals-dir",
        type=Path,
        default=ROOT / "data_candidate" / "signals",
    )
    parser.add_argument(
        "--virology",
        type=Path,
        default=ROOT / "data_candidate" / "virology_municipal_weekly_mt_2026.csv",
    )
    parser.add_argument(
        "--healthcare-pressure",
        type=Path,
        default=None,
        help="CSV institucional opcional. Nunca é exigido para a camada pública.",
    )
    parser.add_argument(
        "--sivep-metadata",
        type=Path,
        default=ROOT / "data_candidate" / "sivep_mt_2026_metadata.json",
    )
    parser.add_argument(
        "--config",
        type=Path,
        default=ROOT / "config" / "territorial_intelligence_v2_1.json",
    )
    parser.add_argument(
        "--out-dir",
        type=Path,
        default=ROOT / "data_candidate" / "territorial_intelligence",
    )
    parser.add_argument("--stable-week", type=int, default=None)
    args = parser.parse_args()

    required = {
        "combined": args.signals_dir / "combined_signals.csv",
        "confidence": args.signals_dir / "signal_confidence.csv",
        "silence": args.signals_dir / "silence_signals.csv",
    }
    missing = [str(path) for path in required.values() if not path.exists()]
    if missing:
        raise FileNotFoundError(
            "Artefatos P2 ausentes: " + ", ".join(missing)
        )
    if not args.sivep_metadata.exists():
        raise FileNotFoundError(f"Metadata SIVEP ausente: {args.sivep_metadata}")

    cfg = json.loads(args.config.read_text(encoding="utf-8"))
    sivep_meta = json.loads(args.sivep_metadata.read_text(encoding="utf-8"))

    stable_week = args.stable_week
    if stable_week is None:
        stable_week = sivep_meta.get("stable_week_provisional")
    if stable_week is None:
        raise ValueError("stable_week não informada e ausente no metadata.")

    combined = pd.read_csv(required["combined"], dtype={"codigo_ibge": "string"})
    confidence = pd.read_csv(required["confidence"], dtype={"codigo_ibge": "string"})
    silence = pd.read_csv(required["silence"], dtype={"codigo_ibge": "string"})

    virology = None
    if args.virology.exists():
        virology = pd.read_csv(args.virology, dtype={"codigo_ibge": "string"})

    pressure = read_optional_csv(args.healthcare_pressure)

    virology_cfg = cfg["dimensions"]["virology"]
    out = build_territorial_intelligence(
        combined_signals=combined,
        confidence=confidence,
        silence=silence,
        stable_week=int(stable_week),
        virology_municipal_weekly=virology,
        healthcare_pressure=pressure,
        virology_window_weeks=int(cfg["reference_window_weeks"]),
        excluded_dominant_agents=virology_cfg["dominant_agent_excludes"],
    )

    args.out_dir.mkdir(parents=True, exist_ok=True)
    csv_path = args.out_dir / "territorial_intelligence_v2_1.csv"
    meta_path = args.out_dir / "territorial_intelligence_v2_1.metadata.json"

    out.to_csv(csv_path, index=False, encoding="utf-8")
    metadata = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "model_id": cfg["model_id"],
        "version": cfg["version"],
        "status": cfg["status"],
        "stable_week": int(stable_week),
        "municipalities": int(out["codigo_ibge"].nunique()),
        "rows": int(len(out)),
        "virology_available": virology is not None and not virology.empty,
        "healthcare_pressure_available": pressure is not None and not pressure.empty,
        "composite_score_enabled": False,
        "operational_alert_enabled": False,
        "validated_for_operational_alert": False,
        "public_promotion_allowed": False,
    }
    meta_path.write_text(
        json.dumps(metadata, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

    print(json.dumps(metadata, ensure_ascii=False, indent=2))
    print(f"output={csv_path}")
    print(f"metadata={meta_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
