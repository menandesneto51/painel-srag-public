# -*- coding: utf-8 -*-
from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from public_data_validation import validate_snapshot


def main() -> int:
    parser = argparse.ArgumentParser(description="Valida os artefatos públicos do Painel SRAG.")
    parser.add_argument("--strict", action="store_true", help="Trata warnings como falha.")
    args = parser.parse_args()

    try:
        issues = validate_snapshot(ROOT)
    except FileNotFoundError as exc:
        print(f"[ERROR] FILE_NOT_FOUND: {exc}")
        return 2
    except Exception as exc:
        print(f"[ERROR] VALIDATION_CRASH: {type(exc).__name__}: {exc}")
        return 2

    if not issues:
        print("OK: nenhuma inconsistência detectada pelos gates automatizados.")
        return 0

    order = {"error": 0, "warning": 1, "info": 2}
    for item in sorted(issues, key=lambda x: (order.get(x["severity"], 9), x["scope"], x["code"])):
        print(f'[{item["severity"].upper()}] {item["scope"]}/{item["code"]}: {item["message"]}')

    errors = sum(i["severity"] == "error" for i in issues)
    warnings = sum(i["severity"] == "warning" for i in issues)
    print(f"\nResumo: {errors} erro(s), {warnings} alerta(s).")

    if errors:
        return 1
    if args.strict and warnings:
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
