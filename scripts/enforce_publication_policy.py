# -*- coding: utf-8 -*-
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from public_data_validation import load_snapshot, validate_loaded_data


def main() -> int:
    data = load_snapshot(ROOT)
    issues = validate_loaded_data(**data)
    errors = [i for i in issues if i["severity"] == "error"]
    warnings = [i for i in issues if i["severity"] == "warning"]

    status = str(data["metadata"].get("publication_status", "")).strip().lower()

    print(f"publication_status={status or 'undefined'}")
    print(f"errors={len(errors)} warnings={len(warnings)}")

    for item in issues:
        print(f'[{item["severity"].upper()}] {item["scope"]}/{item["code"]}: {item["message"]}')

    if status == "validated":
        if errors:
            print("POLICY FAIL: snapshot marcado como validated possui erros bloqueantes.")
            return 1
        print("POLICY PASS: snapshot validated sem erros bloqueantes.")
        return 0

    if status in {"blocked", "under_review"}:
        print("POLICY PASS: snapshot não está liberado para publicação; inconsistências permanecem visíveis e bloqueadas.")
        return 0

    print("POLICY FAIL: publication_status ausente ou desconhecido.")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
