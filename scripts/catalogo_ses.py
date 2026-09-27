#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
from pathlib import Path
from typing import Any

DEFAULT_CONTEXT = "PAINEL-SRAG-PUBLIC"
ENGINE_RELATIVE_PATH = Path("agents") / "ses_data_catalog" / "catalog_agent.py"


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[1]


def _engine_from_root(root: Path) -> Path:
    root = root.expanduser().resolve()
    if root.is_file():
        return root
    return root / ENGINE_RELATIVE_PATH


def _resolve_engine(explicit_agent_root: str | None) -> tuple[Path | None, list[str]]:
    repo_root = _repo_root()
    candidates: list[Path] = []

    if explicit_agent_root:
        candidates.append(_engine_from_root(Path(explicit_agent_root)))

    env_root = os.getenv("SES_DATA_CATALOG_AGENT_ROOT")
    if env_root:
        candidates.append(_engine_from_root(Path(env_root)))

    # Permite um motor local sem tornar obrigatória a cópia do catálogo interno
    # para este repositório público.
    candidates.append(repo_root / ENGINE_RELATIVE_PATH)

    # Convenção útil para workspaces multi-root do Cursor.
    candidates.append(repo_root.parent / "vigia-vsr" / ENGINE_RELATIVE_PATH)

    seen: set[Path] = set()
    checked: list[str] = []
    for candidate in candidates:
        normalized = candidate.expanduser().resolve()
        if normalized in seen:
            continue
        seen.add(normalized)
        checked.append(str(normalized))
        if normalized.is_file():
            return normalized, checked

    return None, checked


def _configuration_block(
    *,
    query: str | None,
    context: str,
    checked: list[str],
) -> dict[str, Any]:
    return {
        "agent": "SES_DATA_CATALOG",
        "status": "configuration_required",
        "preflight_complete": False,
        "can_create_new_source": False,
        "automatic_new_source_authorization": False,
        "project_context": context,
        "query": query,
        "engine_candidates_checked": checked,
        "required_configuration": [
            "Defina SES_DATA_CATALOG_AGENT_ROOT para o clone canônico que contém agents/ses_data_catalog/catalog_agent.py.",
            "Defina SES_DATA_CATALOG_ROOT para o diretório autorizado dos inventários quando ele não for resolvido pelo motor canônico.",
            "No Cursor, não crie fonte/coletor/API/ETL/tabela/indicador/linkage enquanto preflight_complete != true.",
        ],
        "documentation": "docs/SES_DATA_CATALOG_SETUP.md",
        "security": {
            "copy_internal_catalog_into_public_repo": False,
            "pii_exposure_allowed": False,
        },
    }


def _emit(payload: Any) -> None:
    print(json.dumps(payload, ensure_ascii=False, indent=2))


def _self_test(context: str) -> int:
    _emit({
        "agent": "SES_DATA_CATALOG",
        "status": "launcher_ready",
        "preflight_complete": False,
        "project_context": context,
        "python": sys.executable,
        "python_version": sys.version.split()[0],
        "launcher": str(Path(__file__).resolve()),
        "note": "O self-test valida o launcher, não substitui a consulta ao catálogo.",
    })
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Launcher cross-platform do preflight SES_DATA_CATALOG."
    )
    parser.add_argument("--query", help="Necessidade de dados a consultar no Catálogo Mestre.")
    parser.add_argument("--context", default=DEFAULT_CONTEXT)
    parser.add_argument("--agent-root", default=None)
    parser.add_argument("--catalog-root", action="append", default=[])
    parser.add_argument(
        "--strict-config",
        action="store_true",
        help="Retorna código 2 quando o motor canônico não estiver configurado.",
    )
    parser.add_argument(
        "--self-test",
        action="store_true",
        help="Valida apenas que o launcher funciona no Python atual.",
    )
    args = parser.parse_args()

    if args.self_test:
        return _self_test(args.context)

    if not args.query:
        parser.error("--query é obrigatório, exceto com --self-test")

    engine, checked = _resolve_engine(args.agent_root)
    if engine is None:
        _emit(_configuration_block(query=args.query, context=args.context, checked=checked))
        return 2 if args.strict_config else 0

    command = [
        sys.executable,
        str(engine),
        args.query,
        "--context",
        args.context,
    ]

    catalog_roots = list(args.catalog_root)
    if not catalog_roots:
        env_catalog_root = os.getenv("SES_DATA_CATALOG_ROOT")
        if env_catalog_root:
            catalog_roots.append(env_catalog_root)

    for root in catalog_roots:
        command.extend(["--catalog-root", root])

    completed = subprocess.run(
        command,
        check=False,
        capture_output=True,
        text=True,
    )

    if completed.returncode != 0:
        _emit({
            "agent": "SES_DATA_CATALOG",
            "status": "engine_error",
            "preflight_complete": False,
            "can_create_new_source": False,
            "automatic_new_source_authorization": False,
            "project_context": args.context,
            "query": args.query,
            "engine": str(engine),
            "returncode": completed.returncode,
            "stderr": completed.stderr.strip(),
        })
        return completed.returncode

    stdout = completed.stdout.strip()
    try:
        evidence = json.loads(stdout)
    except json.JSONDecodeError:
        _emit({
            "agent": "SES_DATA_CATALOG",
            "status": "invalid_engine_output",
            "preflight_complete": False,
            "can_create_new_source": False,
            "automatic_new_source_authorization": False,
            "project_context": args.context,
            "query": args.query,
            "engine": str(engine),
            "raw_output": stdout,
        })
        return 3

    _emit({
        "agent": "SES_DATA_CATALOG",
        "status": "ok",
        "preflight_complete": True,
        "automatic_new_source_authorization": False,
        "project_context": args.context,
        "engine": str(engine),
        "evidence": evidence,
        "policy": {
            "new_source_requires_human_and_data_governance_review": True,
            "pii_exposure_allowed": False,
            "public_repo_must_not_embed_internal_catalog": True,
        },
    })
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
