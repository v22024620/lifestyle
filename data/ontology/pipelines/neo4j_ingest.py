"""Neo4j + n10s ingestion aligned with graphdb_modules.yml."""
from __future__ import annotations

import argparse
from pathlib import Path
from typing import List

from neo4j import GraphDatabase

if __name__ == "__main__" and __package__ is None:
    import sys
    sys.path.append(str(Path(__file__).resolve().parents[3]))

from data.ontology.pipelines._settings import neo4j_credentials  # type: ignore  # pylint:disable=import-error
from data.ontology.pipelines.config_loader import (  # type: ignore  # pylint:disable=import-error
    ConfigError,
    iter_layer_files,
    resolve_ontology_path,
)

NEO4J_URI, NEO4J_USER, NEO4J_PASSWORD = neo4j_credentials()


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Import LOP ontology TTL into Neo4j using n10s")
    parser.add_argument("--layers", nargs="*", help="Subset of layers to import")
    parser.add_argument("--skip-optional", action="store_true", help="Skip optional dataset layer")
    parser.add_argument("--skip-wipe", action="store_true", help="Keep existing graph data")
    parser.add_argument("--dry-run", action="store_true", help="List file paths without importing")
    return parser.parse_args()


def collect_ttl_paths(args: argparse.Namespace) -> List[Path]:
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
            print(f"[WARN] Missing TTL: {path}")
            continue
        files.append(path)
    if not files:
        raise ConfigError("No TTL files resolved for Neo4j ingest")
    return files


def init_graphconfig(session) -> None:
    config = {
        "handleVocabUris": "SHORTEN",
        "handleMultival": "ARRAY",
        "typesToLabels": True,
        "keepLangTag": False,
        "preserveOriginalUris": True,
        "applyNeo4jNaming": True,
    }
    session.run("CALL n10s.graphconfig.init($config)", config=config)


PREFIX_MAPPINGS = [
    ("lop", "https://lop.apple.com/ontology/lifestyle/core/"),
    ("fibo-fnd", "https://spec.edmcouncil.org/fibo/ontology/FND/"),
    ("fibo-be", "https://spec.edmcouncil.org/fibo/ontology/BE/"),
    ("fibo-fbc", "https://spec.edmcouncil.org/fibo/ontology/FBC/"),
    ("fibo-ind", "https://spec.edmcouncil.org/fibo/ontology/IND/"),
]


def register_prefixes(session) -> None:
    for prefix, namespace in PREFIX_MAPPINGS:
        session.run("CALL n10s.nsprefixes.add($prefix, $namespace)", prefix=prefix, namespace=namespace)


def main() -> None:
    args = parse_args()
    ttl_paths = collect_ttl_paths(args)
    if args.dry_run:
        for path in ttl_paths:
            print(f"[DRY-RUN] {path}")
        return

    driver = GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USER, NEO4J_PASSWORD))
    with driver.session() as session:
        if not args.skip_wipe:
            print("[INFO] Wiping existing graph ...")
            session.run("MATCH (n) DETACH DELETE n")
        print("[INFO] Initializing n10s config ...")
        init_graphconfig(session)
        register_prefixes(session)
        for idx, path in enumerate(ttl_paths, start=1):
            ttl_text = path.read_text(encoding="utf-8")
            print(f"[INFO] ({idx}/{len(ttl_paths)}) Importing {path}")
            session.run("CALL n10s.rdf.import.inline($ttl, 'Turtle')", ttl=ttl_text)
    driver.close()
    print("[INFO] Neo4j ingest completed")


if __name__ == "__main__":
    try:
        main()
    except (ConfigError, Exception) as exc:
        print(f"[ERROR] {exc}")
        raise

