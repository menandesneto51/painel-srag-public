# -*- coding: utf-8 -*-
from __future__ import annotations

import argparse
import json
import re
import sys
from datetime import date, datetime
from pathlib import Path
from urllib.request import Request, urlopen

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_CONFIG = ROOT / "config" / "sources.json"

CSV_PATTERN = re.compile(
    r"/SRAG/2026/INFLUD26-(?P<day>\d{2})-(?P<month>\d{2})-(?P<year>\d{4})\.csv(?:$|\?)",
    re.IGNORECASE,
)


def parse_date_from_url(url: str) -> date | None:
    match = CSV_PATTERN.search(url or "")
    if not match:
        return None
    return date(
        int(match.group("year")),
        int(match.group("month")),
        int(match.group("day")),
    )


def fetch_json(url: str, timeout: int = 60) -> dict:
    request = Request(url, headers={"User-Agent": "painel-srag-public-v2/source-watch"})
    with urlopen(request, timeout=timeout) as response:
        return json.loads(response.read().decode("utf-8"))


def latest_2026_csv(resources: list[dict]) -> dict | None:
    candidates = []
    for resource in resources:
        url = str(resource.get("url") or "")
        resource_date = parse_date_from_url(url)
        fmt = str(resource.get("format") or "").upper()
        if resource_date and (fmt == "CSV" or url.lower().endswith(".csv")):
            candidates.append((resource_date, resource))
    if not candidates:
        return None
    candidates.sort(key=lambda item: item[0], reverse=True)
    resource_date, resource = candidates[0]
    return {
        "resource_date": resource_date.isoformat(),
        "name": resource.get("name"),
        "url": resource.get("url"),
        "id": resource.get("id"),
        "last_modified": resource.get("last_modified"),
    }


def check(config_path: Path) -> tuple[int, dict]:
    config = json.loads(config_path.read_text(encoding="utf-8"))
    pinned = config["sources"]["sivep_gripe_2026"]
    pinned_date = date.fromisoformat(pinned["resource_date"])

    api = pinned.get("ckan_api")
    if not api:
        raise ValueError("ckan_api ausente em config/sources.json")

    payload = fetch_json(api)
    if payload.get("success") is not True:
        raise RuntimeError("CKAN API respondeu success != true")

    result = payload.get("result") or {}
    latest = latest_2026_csv(result.get("resources") or [])
    if latest is None:
        raise RuntimeError("Nenhum recurso CSV 2026 reconhecido no catálogo CKAN.")

    latest_date = date.fromisoformat(latest["resource_date"])
    status = "current"
    exit_code = 0
    if latest_date > pinned_date:
        status = "update_available"
        exit_code = 3
    elif latest_date < pinned_date:
        status = "catalog_older_than_pin"
        exit_code = 2

    report = {
        "checked_at": datetime.utcnow().isoformat(timespec="seconds") + "Z",
        "status": status,
        "pinned": {
            "resource_date": pinned["resource_date"],
            "url": pinned["url"],
            "resource_id": pinned.get("resource_id"),
        },
        "latest": latest,
    }
    return exit_code, report


def main() -> int:
    parser = argparse.ArgumentParser(description="Verifica se há CSV SIVEP-Gripe 2026 mais novo no OpenDataSUS.")
    parser.add_argument("--config", type=Path, default=DEFAULT_CONFIG)
    parser.add_argument("--output", type=Path, default=None)
    args = parser.parse_args()

    code, report = check(args.config)
    rendered = json.dumps(report, ensure_ascii=False, indent=2)
    print(rendered)
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(rendered + "\n", encoding="utf-8")
    return code


if __name__ == "__main__":
    raise SystemExit(main())
