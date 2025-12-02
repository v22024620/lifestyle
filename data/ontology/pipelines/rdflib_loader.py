"""Load TTL files defined in graphdb_modules.yml using rdflib."""
from __future__ import annotations

import argparse
import sys
from typing import Iterable, List, Sequence

from rdflib import Graph

if __name__ == "__main__" and __package__ is None:
    import pathlib

    sys.path.append(str(pathlib.Path(__file__).resolve().parents[3]))

from data.ontology.pipelines.config_loader import (  # type: ignore  # pylint:disable=import-error
    ConfigError,
    iter_layer_files,
    resolve_ontology_path,
)


def _collect_files(include_optional: bool, layer_filter: Sequence[str] | None) -> List[str]:
    return list(
        iter_layer_files(
            include_optional=include_optional,
            only_layers=layer_filter,
        )
    )


def load_graph(files: Iterable[str] | None = None) -> Graph:
    graph = Graph()
    targets = list(files) if files else _collect_files(include_optional=True, layer_filter=None)
    for relative in targets:
        ttl_path = resolve_ontology_path(relative)
        if not ttl_path.exists():
            print(f"[WARN] Missing TTL skipped: {ttl_path}")
            continue
        print(f"[INFO] Loading {ttl_path}")
        graph.parse(ttl_path)
    print(f"[INFO] Triples loaded: {len(graph)}")
    return graph


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="rdflib loader for LOP ontology")
    parser.add_argument("--layers", nargs="*", help="Limit to specific layer names")
    parser.add_argument("--skip-optional", action="store_true", help="Skip optional layers")
    parser.add_argument("--list", action="store_true", help="List files without loading")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    files = _collect_files(include_optional=not args.skip_optional, layer_filter=args.layers)
    if args.list:
        print("[INFO] Files in load order:")
        for relative in files:
            print(f" - {relative}")
        return
    load_graph(files)


if __name__ == "__main__":
    try:
        main()
    except ConfigError as exc:
        print(f"[ERROR] {exc}")
        sys.exit(1)

