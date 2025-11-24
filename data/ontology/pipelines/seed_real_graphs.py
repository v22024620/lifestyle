"""Seed GraphDB and Neo4j with LOP ontology modules + Apple Fitness dataset."""
from __future__ import annotations

import argparse
from pathlib import Path
from typing import Iterable, List

import httpx
from neo4j import GraphDatabase

from data.ontology.pipelines.apple_fitness_dataset import DATASET_PATH, write_dataset
from data.ontology.pipelines._settings import load_settings

ONTOLOGY_ROOT = Path(__file__).resolve().parents[1]
SETTINGS = load_settings()

DEFAULT_LOAD_ORDER = [
    "md/LOPFitness-Metadata.ttl",
    "fnd/Agents/LOPAgents.ttl",
    "fnd/Arrangements/LOPContracts.ttl",
    "fnd/DatesAndTimes/LOPTime.ttl",
    "be/Organizations/Studios.ttl",
    "be/FunctionalEntities/TrainerNetworks.ttl",
    "bp/Engagements/ProgramLifecycle.ttl",
    "cae/ProgramParticipationAgreement.ttl",
    "fbc/Products/FitnessSubscriptions.ttl",
    "fbc/Accounting/FitnessSettlement.ttl",
    "der/FitnessRiskDerivedMetrics.ttl",
    "ind/Insurance/FitnessRisk.ttl",
    "loan/StudioCapexLoans.ttl",
    "sec/FitnessReceivablesSecuritization.ttl",
    "extensions/lop-lifestyle/LOPFitness-Core.ttl",
    "extensions/lop-lifestyle/LOPFitness-Programs.ttl",
    "extensions/lop-lifestyle/LOPFitness-Individuals.ttl",
    "extensions/lop-lifestyle/fibo_core_subset.ttl",
    "extensions/lop-lifestyle/fibo_lifestyle_extension.ttl",
    "datasets/apple_fitness.ttl",
]


def _compute_load_paths() -> List[Path]:
    return [ONTOLOGY_ROOT / relative for relative in DEFAULT_LOAD_ORDER]


def seed_graphdb(endpoint: str, repository: str, ttl_paths: Iterable[Path]) -> None:
    base = endpoint.rstrip("/")
    for path in ttl_paths:
        if not path.exists():
            print(f"[WARN] Skip missing TTL for GraphDB: {path}")
            continue
        target = f"{base}/repositories/{repository}/statements"
        print(f"[GraphDB] Loading {path.relative_to(ONTOLOGY_ROOT)}")
        with path.open("rb") as payload:
            resp = httpx.post(
                target,
                content=payload.read(),
                headers={"Content-Type": "text/turtle"},
                timeout=60,
            )
            resp.raise_for_status()


def _ensure_n10s(session) -> None:
    config = {
        "handleVocabUris": "SHORTEN",
        "typesToLabels": True,
        "keepLangTag": True,
        "handleMultival": "OVERWRITE",
    }
    result = session.run("CALL n10s.graphconfig.show()")
    if result.peek() is None:
        session.run("CALL n10s.graphconfig.init($config)", config=config)


def seed_neo4j(uri: str, user: str, password: str, ttl_paths: Iterable[Path], reset: bool) -> None:
    driver = GraphDatabase.driver(uri, auth=(user, password))
    with driver.session() as session:
        if reset:
            print("[Neo4j] Clearing existing nodes and relationships")
            session.run("MATCH (n) DETACH DELETE n")
        _ensure_n10s(session)
        for path in ttl_paths:
            if not path.exists():
                print(f"[WARN] Skip missing TTL for Neo4j: {path}")
                continue
            print(f"[Neo4j] Importing {path.relative_to(ONTOLOGY_ROOT)}")
            payload = path.read_text(encoding="utf-8")
            session.run("CALL n10s.rdf.import.inline($payload, 'Turtle')", payload=payload)
    driver.close()


def cli(argv: Iterable[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description="Seed GraphDB + Neo4j with full ontology + Apple dataset")
    parser.add_argument("--graphdb-endpoint", default=SETTINGS.graphdb_endpoint)
    parser.add_argument("--graphdb-repository", default="fibo")
    parser.add_argument("--neo4j-uri", default=SETTINGS.neo4j_uri)
    parser.add_argument("--neo4j-user", default=SETTINGS.neo4j_user)
    parser.add_argument("--neo4j-password", default=SETTINGS.neo4j_password)
    parser.add_argument("--skip-graphdb", action="store_true")
    parser.add_argument("--skip-neo4j", action="store_true")
    parser.add_argument("--reset-neo4j", action="store_true")
    parser.add_argument("--refresh-dataset", action="store_true", help="Regenerate apple_fitness.ttl before seeding")
    args = parser.parse_args(list(argv) if argv is not None else None)

    if not args.neo4j_password:
        raise RuntimeError("Set LCP_NEO4J_PASSWORD in .env or pass --neo4j-password")

    if args.refresh_dataset or not DATASET_PATH.exists():
        print("[DATA] Rebuilding apple_fitness.ttl")
        write_dataset()

    ttl_paths = _compute_load_paths()

    if not args.skip_graphdb:
        seed_graphdb(args.graphdb_endpoint, args.graphdb_repository, ttl_paths)
    else:
        print("[GraphDB] Skipped")

    if not args.skip_neo4j:
        seed_neo4j(args.neo4j_uri, args.neo4j_user, args.neo4j_password, ttl_paths, args.reset_neo4j)
    else:
        print("[Neo4j] Skipped")


if __name__ == "__main__":
    cli()
