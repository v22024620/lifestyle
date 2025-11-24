"""Builds a lightweight entity index from LOP TTL modules."""
from __future__ import annotations

import json
from pathlib import Path
from typing import List

from rdflib import Graph, RDF, RDFS, OWL

BASE_DIR = Path(__file__).resolve().parent.parent
INDEX_PATH = BASE_DIR / "datasets" / "entity_index.json"
TTL_MODULES = [
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
]


def load_graph(paths: List[str]) -> Graph:
    graph = Graph()
    for rel in paths:
        ttl_path = BASE_DIR / rel
        if not ttl_path.exists():
            print(f"[WARN] skip missing {ttl_path}")
            continue
        graph.parse(ttl_path)
    return graph


def extract_entities(graph: Graph) -> list:
    entries = []
    for cls in graph.subjects(RDF.type, OWL.Class):
        iri = str(cls)
        if not iri.startswith("https://lop.com"):
            continue
        label = graph.value(cls, RDFS.label)
        comment = graph.value(cls, RDFS.comment) or graph.value(cls, RDFS.isDefinedBy)
        entries.append({
            "iri": iri,
            "label": str(label) if label else None,
            "comment": str(comment) if comment else None,
        })
    return entries


def main() -> None:
    graph = load_graph(TTL_MODULES)
    entries = extract_entities(graph)
    INDEX_PATH.write_text(json.dumps({"entities": entries}, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"[INFO] entity index saved to {INDEX_PATH}")


if __name__ == "__main__":
    main()
