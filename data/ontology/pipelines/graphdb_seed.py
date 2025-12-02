"""GraphDB seed helper driven by graphdb_modules.yml."""
from __future__ import annotations

import argparse
import os
import sys
import time
from pathlib import Path
from typing import List

import httpx

if __name__ == "__main__" and __package__ is None:
    sys.path.append(str(Path(__file__).resolve().parents[3]))

from data.ontology.pipelines import rdflib_loader  # type: ignore  # pylint:disable=import-error
from data.ontology.pipelines.config_loader import (  # type: ignore  # pylint:disable=import-error
    ConfigError,
    iter_layer_files,
    resolve_ontology_path,
)

DEFAULT_ENDPOINT = os.environ.get("GRAPHDB_ENDPOINT")
DEFAULT_REPOSITORY = os.environ.get("GRAPHDB_REPOSITORY")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Seed GraphDB with LOP ontology")
    parser.add_argument("--endpoint", default=DEFAULT_ENDPOINT, help="GraphDB endpoint base URL")
    parser.add_argument("--repository", default=DEFAULT_REPOSITORY, help="Repository ID")
    parser.add_argument("--layers", nargs="*", help="Subset of layers to load")
    parser.add_argument("--skip-optional", action="store_true", help="Skip optional datasets layer")
    parser.add_argument("--validate", action="store_true", help="Run rdflib validation before POSTing")
    parser.add_argument("--dry-run", action="store_true", help="Print actions without uploading")
    parser.add_argument("--delay", type=float, default=0.0, help="Delay between requests")
    return parser.parse_args()


def collect_files(args: argparse.Namespace) -> List[Path]:
    relatives = list(
        iter_layer_files(
            include_optional=not args.skip_optional,
            only_layers=args.layers,
        )
    )
    files: List[Path] = []
    for rel in relatives:
        path = resolve_ontology_path(rel)
        if not path.exists():
            print(f"[WARN] Skipping missing file: {path}")
            continue
        files.append(path)
    if not files:
        raise ConfigError("No TTL files resolved for GraphDB seeding")
    return files


def post_file(client: httpx.Client, url: str, ttl_path: Path, dry_run: bool) -> None:
    if dry_run:
        print(f"[DRY-RUN] Would POST {ttl_path} -> {url}")
        return
    response = client.post(
        url,
        headers={"Content-Type": "application/x-turtle"},
        content=ttl_path.read_bytes(),
        timeout=60.0,
    )
    response.raise_for_status()
    print(f"[INFO] Loaded {ttl_path.name}")


def main() -> None:
    args = parse_args()
    if not args.endpoint or not args.repository:
        raise ConfigError("endpoint and repository must be provided")
    files = collect_files(args)

    if args.validate:
        relatives = [str(path.relative_to(resolve_ontology_path("."))) for path in files]
        rdflib_loader.load_graph(relatives)

    base_url = args.endpoint.rstrip("/") + f"/repositories/{args.repository}/statements"
    with httpx.Client() as client:
        for ttl_path in files:
            post_file(client, base_url, ttl_path, args.dry_run)
            if args.delay:
                time.sleep(args.delay)
    print(f"[INFO] Completed GraphDB seeding ({len(files)} files)")


if __name__ == "__main__":
    try:
        main()
    except (ConfigError, httpx.HTTPError) as exc:
        print(f"[ERROR] {exc}")
        sys.exit(1)

