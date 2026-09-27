# -*- coding: utf-8 -*-
from __future__ import annotations

import argparse
import json
import shutil
import sys
import tempfile
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from public_data_validation import validate_snapshot


REQUIRED_PUBLIC_FILES = {
    "metadata_public.json",
    "kpis.json",
    "weekly_summary.csv",
    "risk_summary.csv",
    "risk_summary_v2_candidate.csv",
    "silent_summary.csv",
    "virology_summary.csv",
    "forecast_summary.csv",
    "or_obito_summary.csv",
    "or_uti_summary.csv",
}


def validate_approval(path: Path) -> dict:
    if not path.exists():
        raise FileNotFoundError(f"Arquivo de aprovação não encontrado: {path}")

    approval = json.loads(path.read_text(encoding="utf-8"))
    required_true = (
        "approved",
        "epidemiology_review",
        "statistical_review",
        "privacy_review",
    )
    for key in required_true:
        if approval.get(key) is not True:
            raise ValueError(f"Aprovação inválida: {key} deve ser true.")

    for key in ("approver", "approved_at", "snapshot_id"):
        if not str(approval.get(key, "")).strip():
            raise ValueError(f"Aprovação deve registrar {key}.")

    return approval


def validate_candidate_approval_state(candidate_dir: Path, approval: dict) -> dict:
    metadata_path = candidate_dir / "metadata_public.json"
    if not metadata_path.exists():
        raise FileNotFoundError(f"metadata_public.json ausente em {candidate_dir}")

    metadata = json.loads(metadata_path.read_text(encoding="utf-8"))
    if str(metadata.get("publication_status", "")).strip().lower() != "validated":
        raise ValueError(
            "Snapshot candidato ainda não está validated. "
            "Execute scripts/approve_candidate_snapshot.py antes da promoção."
        )

    embedded = metadata.get("approval") or {}
    for key in ("snapshot_id", "approver", "approved_at"):
        if str(embedded.get(key, "")) != str(approval.get(key, "")):
            raise ValueError(
                f"Aprovação embutida no metadata diverge do approval-file em {key}."
            )
    return metadata


def validate_candidate_set(candidate_dir: Path) -> list[dict[str, str]]:
    existing = {p.name for p in candidate_dir.iterdir() if p.is_file()}
    missing = REQUIRED_PUBLIC_FILES.difference(existing)
    if missing:
        raise ValueError(
            "Snapshot candidato incompleto. Arquivos ausentes: "
            + ", ".join(sorted(missing))
        )

    with tempfile.TemporaryDirectory(prefix="srag-public-validation-") as tmp:
        staged_root = Path(tmp)
        staged_public = staged_root / "data_public"
        staged_public.mkdir(parents=True)

        for name in REQUIRED_PUBLIC_FILES:
            shutil.copy2(candidate_dir / name, staged_public / name)

        issues = validate_snapshot(staged_root)
        blocking = [i for i in issues if i["severity"] == "error"]
        if blocking:
            messages = "; ".join(
                f'{i["scope"]}/{i["code"]}: {i["message"]}' for i in blocking
            )
            raise RuntimeError(
                "Snapshot candidato reprovado antes da promoção: " + messages
            )
        return issues


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Promove snapshot completo somente após pré-validação e aprovação explícita."
    )
    parser.add_argument("--candidate-dir", type=Path, default=ROOT / "data_candidate" / "public_snapshot")
    parser.add_argument("--public-dir", type=Path, default=ROOT / "data_public")
    parser.add_argument("--approval-file", type=Path, required=True)
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    if not args.candidate_dir.exists():
        raise FileNotFoundError(f"Diretório candidato não encontrado: {args.candidate_dir}")

    approval = validate_approval(args.approval_file)

    validate_candidate_approval_state(args.candidate_dir, approval)
    issues = validate_candidate_set(args.candidate_dir)

    print(f"snapshot_id={approval['snapshot_id']}")
    print(f"approver={approval['approver']}")
    print(f"approved_at={approval['approved_at']}")
    print(f"pre_validation_issues={len(issues)}")
    print("candidate_files:")
    for name in sorted(REQUIRED_PUBLIC_FILES):
        print(f"  - {name}")

    if args.dry_run:
        print("DRY RUN: snapshot completo aprovado na pré-validação; nenhum arquivo copiado.")
        return 0

    args.public_dir.mkdir(parents=True, exist_ok=True)

    # Só escreve depois de todo o conjunto candidato ter sido validado.
    for name in sorted(REQUIRED_PUBLIC_FILES):
        shutil.copy2(args.candidate_dir / name, args.public_dir / name)

    audit = {
        "snapshot_id": approval["snapshot_id"],
        "approver": approval["approver"],
        "approved_at": approval["approved_at"],
        "promoted_at": datetime.now(timezone.utc).isoformat(),
        "files": sorted(REQUIRED_PUBLIC_FILES),
    }
    (args.public_dir / "promotion_audit.json").write_text(
        json.dumps(audit, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

    print("Promoção concluída. O conjunto foi pré-validado antes de qualquer cópia.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
