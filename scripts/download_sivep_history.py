# -*- coding: utf-8 -*-
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from urllib.request import Request, urlopen

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_CONFIG = ROOT / "config" / "sivep_history_sources.json"
DEFAULT_OUT = ROOT / "data_raw" / "sivep_history"


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        while True:
            chunk = handle.read(1024 * 1024)
            if not chunk:
                break
            digest.update(chunk)
    return digest.hexdigest()


def download(url: str, destination: Path) -> None:
    destination.parent.mkdir(parents=True, exist_ok=True)
    request = Request(url, headers={"User-Agent": "painel-srag-public-v2/history"})
    with urlopen(request, timeout=180) as response, destination.open("wb") as target:
        while True:
            chunk = response.read(1024 * 1024)
            if not chunk:
                break
            target.write(chunk)


def main() -> int:
    parser = argparse.ArgumentParser(description="Baixa snapshots anuais SIVEP-Gripe usados no baseline.")
    parser.add_argument("--config", type=Path, default=DEFAULT_CONFIG)
    parser.add_argument("--out", type=Path, default=DEFAULT_OUT)
    parser.add_argument("--years", nargs="*", type=int, default=None)
    parser.add_argument("--force", action="store_true")
    args = parser.parse_args()

    cfg = json.loads(args.config.read_text(encoding="utf-8"))
    history = cfg["history"]
    selected = sorted(history)
    if args.years:
        requested = {str(y) for y in args.years}
        unknown = requested.difference(history)
        if unknown:
            raise ValueError(f"Anos não configurados: {sorted(unknown)}")
        selected = sorted(requested)

    manifest = {"files": {}}
    for year in selected:
        source = history[year]
        destination = args.out / source["local_filename"]
        if not destination.exists() or args.force:
            print(f"[DOWNLOAD] {year}: {source['url']}")
            download(source["url"], destination)
        else:
            print(f"[SKIP] {year}: {destination}")

        manifest["files"][year] = {
            "path": str(destination),
            "bytes": destination.stat().st_size,
            "sha256": sha256_file(destination),
            "resource_date": source["resource_date"],
            "url": source["url"],
        }

    manifest_path = args.out / "history_manifest.json"
    manifest_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"[MANIFEST] {manifest_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
