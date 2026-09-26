# -*- coding: utf-8 -*-
from __future__ import annotations

import argparse
import json
import shutil
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from public_data_validation import validate_snapshot


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Promove artefatos candidatos somente após validação explícita."
    )
    parser.add_argument("--candidate-dir", type=Path, default=ROOT / "data_candidate")
    parser.add_argument("--public-dir", type=Path, default=ROOT / "data_public")
    parser.add_argument("--approval-file", type=Path, required=True)
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    if not args.approval_file.exists():
        raise FileNotFoundError(f"Arquivo de aprovação não encontrado: {args.approval_file}")

    approval = json.loads(args.approval_file.read_text(encoding="utf-8"))
    required = {
        "approved": True,
        "epidemiology_review": True,
        "statistical_review": True,
        "privacy_review": True,
    }
    for key, expected in required.items():
        if approval.get(key) is not expected:
            raise ValueError(f"Aprovação inválida: {key} deve ser {expected}.")

    approver = str(approval.get("approver", "")).strip()
    approved_at = str(approval.get("approved_at", "")).strip()
    snapshot_id = str(approval.get("snapshot_id", "")).strip()
    if not approver or not approved_at or not snapshot_id:
        raise ValueError("Aprovação deve registrar approver, approved_at e snapshot_id.")

    candidate_files = sorted(p for p in args.candidate_dir.glob("*") if p.is_file())
    if not candidate_files:
        raise ValueError(f"Nenhum artefato candidato encontrado em {args.candidate_dir}")

    print(f"snapshot_id={snapshot_id}")
    print(f"approver={approver}")
    print(f"approved_at={approved_at}")
    print("candidate_files:")
    for path in candidate_files:
        print(f"  - {path.name}")

    if args.dry_run:
        print("DRY RUN: nenhum arquivo promovido.")
        return 0

    args.public_dir.mkdir(parents=True, exist_ok=True)
    for source in candidate_files:
        shutil.copy2(source, args.public_dir / source.name)

    audit = {
        "snapshot_id": snapshot_id,
        "approver": approver,
        "approved_at": approved_at,
        "promoted_at": datetime.now(timezone.utc).isoformat(),
        "files": [p.name for p in candidate_files],
    }
    (args.public_dir / "promotion_audit.json").write_text(
        json.dumps(audit, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

    issues = validate_snapshot(ROOT)
    blocking = [i for i in issues if i["severity"] == "error"]
    if blocking:
        raise RuntimeError(
            "Promoção copiou os arquivos, mas os gates públicos ainda encontraram erros. "
            "Reverta a promoção antes de liberar publicação."
        )

    print("Promoção concluída e gates públicos sem erros bloqueantes.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
