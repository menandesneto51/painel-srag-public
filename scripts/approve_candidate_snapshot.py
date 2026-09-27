# -*- coding: utf-8 -*-
from __future__ import annotations

import argparse
import json
import shutil
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from public_data_validation import validate_snapshot
from scripts.promote_snapshot import REQUIRED_PUBLIC_FILES, validate_approval


def prevalidate_under_review(candidate_dir: Path) -> list[dict[str, str]]:
    existing = {p.name for p in candidate_dir.iterdir() if p.is_file()}
    missing = REQUIRED_PUBLIC_FILES.difference(existing)
    if missing:
        raise ValueError(
            "Snapshot candidato incompleto. Arquivos ausentes: "
            + ", ".join(sorted(missing))
        )

    with tempfile.TemporaryDirectory(prefix="srag-candidate-review-") as tmp:
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
                "Snapshot candidato possui erros bloqueantes e não pode ser aprovado: "
                + messages
            )
        return issues


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Marca snapshot candidato como validated somente após aprovação formal."
    )
    parser.add_argument(
        "--candidate-dir",
        type=Path,
        default=ROOT / "data_candidate" / "public_snapshot",
    )
    parser.add_argument("--approval-file", type=Path, required=True)
    args = parser.parse_args()

    if not args.candidate_dir.exists():
        raise FileNotFoundError(args.candidate_dir)

    approval = validate_approval(args.approval_file)
    issues = prevalidate_under_review(args.candidate_dir)

    metadata_path = args.candidate_dir / "metadata_public.json"
    metadata = json.loads(metadata_path.read_text(encoding="utf-8"))
    current = str(metadata.get("publication_status", "")).strip().lower()
    if current not in {"under_review", "blocked"}:
        raise ValueError(
            f"publication_status deve estar under_review/blocked antes da aprovação; atual={current!r}"
        )

    metadata["publication_status"] = "validated"
    metadata["validation_status"] = "validated"
    metadata["approval"] = {
        "snapshot_id": approval["snapshot_id"],
        "approver": approval["approver"],
        "approved_at": approval["approved_at"],
        "epidemiology_review": True,
        "statistical_review": True,
        "privacy_review": True,
        "notes": approval.get("notes", ""),
    }
    metadata["preapproval_issue_count"] = len(issues)

    metadata_path.write_text(
        json.dumps(metadata, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    print(
        f"Snapshot {approval['snapshot_id']} marcado como validated em {metadata_path}."
    )
    print("Execute agora scripts/promote_snapshot.py com o mesmo approval-file.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
