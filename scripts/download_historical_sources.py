# -*- coding: utf-8 -*-
from __future__ import annotations

import argparse
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
from urllib.request import Request, urlopen

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_CONFIG = ROOT / "config" / "historical_sources.json"
DEFAULT_OUT = ROOT / "data_raw" / "historical"


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def download(url: str, destination: Path) -> None:
    destination.parent.mkdir(parents=True, exist_ok=True)
    request = Request(url, headers={"User-Agent": "painel-srag-public-v2-p2/1.0"})
    with urlopen(request, timeout=180) as response, destination.open("wb") as output:
        for chunk in iter(lambda: response.read(1024 * 1024), b""):
            output.write(chunk)


def parse_years(value: str, available: set[int]) -> list[int]:
    if value.strip().lower() == "all":
        return sorted(available)
    years = sorted({int(x.strip()) for x in value.split(",") if x.strip()})
    invalid = [year for year in years if year not in available]
    if invalid:
        raise ValueError(f"Anos não configurados: {invalid}")
    return years


def main() -> int:
    parser = argparse.ArgumentParser(description="Baixa snapshots históricos oficiais do SIVEP-Gripe.")
    parser.add_argument("--config", type=Path, default=DEFAULT_CONFIG)
    parser.add_argument("--years", default="all", help="Ex.: 2019,2023,2024 ou all")
    parser.add_argument("--out", type=Path, default=DEFAULT_OUT)
    parser.add_argument("--force", action="store_true")
    args = parser.parse_args()

    config = json.loads(args.config.read_text(encoding="utf-8"))
    configured = {int(year) for year in config["sources"]}
    years = parse_years(args.years, configured)

    manifest = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "config": str(args.config),
        "files": {},
    }

    for year in years:
        source = config["sources"][str(year)]
        destination = args.out / source["local_filename"]
        if destination.exists() and not args.force:
            print(f"[SKIP] {year}: {destination}")
        else:
            print(f"[DOWNLOAD] {year}: {source['url']}")
            download(source["url"], destination)

        manifest["files"][str(year)] = {
            "path": str(destination),
            "bytes": destination.stat().st_size,
            "sha256": sha256_file(destination),
            "resource_date": source["resource_date"],
            "resource_id": source["resource_id"],
            "source_url": source["url"],
        }

    manifest_path = args.out / "historical_source_manifest.json"
    manifest_path.write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    print(f"[MANIFEST] {manifest_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
