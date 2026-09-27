# -*- coding: utf-8 -*-
from __future__ import annotations

import argparse
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
from urllib.request import Request, urlopen

ROOT = Path(__file__).resolve().parents[1]
CATALOG = ROOT / "config" / "sources.json"
DEFAULT_OUT = ROOT / "data_raw"


def sha256_file(path: Path, chunk_size: int = 1024 * 1024) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        while True:
            chunk = handle.read(chunk_size)
            if not chunk:
                break
            digest.update(chunk)
    return digest.hexdigest()


def download(url: str, destination: Path) -> None:
    destination.parent.mkdir(parents=True, exist_ok=True)
    request = Request(url, headers={"User-Agent": "painel-srag-public-v2/1.0"})
    with urlopen(request, timeout=120) as response, destination.open("wb") as output:
        while True:
            chunk = response.read(1024 * 1024)
            if not chunk:
                break
            output.write(chunk)


def main() -> int:
    parser = argparse.ArgumentParser(description="Baixa fontes oficiais pinadas para o reprocessamento SRAG v2.")
    parser.add_argument("--source", choices=["all", "sivep_gripe_2026", "ibge_population_2026"], default="all")
    parser.add_argument("--out", type=Path, default=DEFAULT_OUT)
    parser.add_argument("--force", action="store_true")
    args = parser.parse_args()

    catalog = json.loads(CATALOG.read_text(encoding="utf-8"))
    selected = catalog["sources"]
    if args.source != "all":
        selected = {args.source: selected[args.source]}

    manifest = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "catalog": str(CATALOG.relative_to(ROOT)),
        "files": {},
    }

    for key, source in selected.items():
        destination = args.out / source["local_filename"]

        if destination.exists() and not args.force:
            print(f"[SKIP] {key}: {destination} já existe. Use --force para baixar novamente.")
        else:
            print(f"[DOWNLOAD] {key}: {source['url']}")
            download(source["url"], destination)

        manifest["files"][key] = {
            "path": str(destination),
            "bytes": destination.stat().st_size,
            "sha256": sha256_file(destination),
            "source_url": source["url"],
            "resource_date": source.get("resource_date") or source.get("reference_date"),
        }
        print(f"[OK] {key}: {manifest['files'][key]['bytes']} bytes")

    manifest_path = args.out / "source_manifest.json"
    manifest_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"[MANIFEST] {manifest_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
