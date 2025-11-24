"""Ontology service: load TTLs, query GraphDB/local graph, and map to Neo4j payloads."""
from __future__ import annotations

import logging
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional

try:
    from rdflib import Graph, URIRef, RDFS  # type: ignore
except ImportError:  # pragma: no cover - optional dependency
    Graph = None  # type: ignore
    URIRef = None  # type: ignore
    RDFS = None  # type: ignore

try:
    from SPARQLWrapper import SPARQLWrapper, JSON  # type: ignore
except ImportError:  # pragma: no cover - optional dependency
    SPARQLWrapper = None  # type: ignore
    JSON = None  # type: ignore

logger = logging.getLogger(__name__)


class OntologyService:
    """Ontology management using rdflib + GraphDB endpoint with graceful fallbacks."""

    def __init__(self, graphdb_endpoint: str, ttl_paths: Optional[Iterable[str]] = None):
        self.graphdb_endpoint = graphdb_endpoint
        self.ttl_paths = list(ttl_paths or [
            "data/ontology/md/LOPFitness-Metadata.ttl",
            "data/ontology/fnd/Agents/LOPAgents.ttl",
            "data/ontology/fnd/Arrangements/LOPContracts.ttl",
            "data/ontology/fnd/DatesAndTimes/LOPTime.ttl",
            "data/ontology/be/Organizations/Studios.ttl",
            "data/ontology/be/FunctionalEntities/TrainerNetworks.ttl",
            "data/ontology/bp/Engagements/ProgramLifecycle.ttl",
            "data/ontology/cae/ProgramParticipationAgreement.ttl",
            "data/ontology/fbc/Products/FitnessSubscriptions.ttl",
            "data/ontology/fbc/Accounting/FitnessSettlement.ttl",
            "data/ontology/der/FitnessRiskDerivedMetrics.ttl",
            "data/ontology/ind/Insurance/FitnessRisk.ttl",
            "data/ontology/loan/StudioCapexLoans.ttl",
            "data/ontology/sec/FitnessReceivablesSecuritization.ttl",
            "data/ontology/extensions/lop-lifestyle/LOPFitness-Core.ttl",
            "data/ontology/extensions/lop-lifestyle/LOPFitness-Programs.ttl",
            "data/ontology/extensions/lop-lifestyle/LOPFitness-Individuals.ttl",
            "data/ontology/extensions/lop-lifestyle/fibo_core_subset.ttl",
            "data/ontology/extensions/lop-lifestyle/fibo_lifestyle_extension.ttl",
            "data/ontology/datasets/provider_metrics.ttl",
            "data/ontology/datasets/risk-events.ttl",
            "data/ontology/datasets/SGANG01.ttl",
            "data/ontology/datasets/apple_fitness.ttl",
        ])
        self.graph: Optional[Graph] = Graph() if Graph else None
        self._last_loaded_at: Optional[str] = None

    # ---------- Load & merge ----------
    def load_ontologies(self) -> None:
        """Load TTL files into an rdflib graph."""
        if self.graph is None:
            logger.warning("rdflib not installed; skipping ontology load")
            return
        loaded = 0
        for ttl_path in self.ttl_paths:
            path = Path(ttl_path)
            if not path.exists():
                logger.warning("TTL file not found: %s", path)
                continue
            try:
                self.graph.parse(path.as_posix(), format="turtle")
                loaded += 1
            except Exception as err:  # pragma: no cover
                logger.warning("Failed to parse TTL %s: %s", path, err)
        logger.info("Loaded %s TTL files into graph", loaded)
        if loaded:
            self._last_loaded_at = datetime.utcnow().isoformat()

    def ensure_ready(self) -> None:
        """Ensure TTLs are loaded into the local graph."""
        if self.graph is not None and len(self.graph) == 0:
            self.load_ontologies()

    def is_connected(self) -> bool:
        return self.graph is not None and len(self.graph) > 0

    def merge_graphs(self) -> Dict[str, Any]:
        """Return metadata describing merged graph."""
        if not self.graph:
            return {"status": "rdflib-missing", "triples": 0}
        return {"status": "merged", "triples": len(self.graph), "last_loaded_at": self._last_loaded_at}

    def status_summary(self) -> Dict[str, Any]:
        """Surface summary metadata for UI layers."""
        merged = self.merge_graphs()
        return {"triples": merged.get("triples", 0), "last_loaded_at": merged.get("last_loaded_at")}

    # ---------- Query ----------
    def _query_local_graph(self, query: str) -> List[Dict[str, Any]]:
        if not self.graph:
            return []
        try:
            results = self.graph.query(query)
            rows: List[Dict[str, Any]] = []
            for row in results:  # type: ignore[assignment]
                rows.append({str(var): str(val) for var, val in row.asdict().items()})
            return rows
        except Exception as err:  # pragma: no cover
            logger.warning("Local SPARQL query failed: %s", err)
            return []

    def sparql_query(self, query: str) -> List[Dict[str, Any]]:
        """Execute SPARQL query against GraphDB; fallback to local rdflib graph."""
        if SPARQLWrapper and self.graphdb_endpoint:
            try:
                sparql = SPARQLWrapper(self.graphdb_endpoint)
                sparql.setReturnFormat(JSON)
                sparql.setQuery(query)
                response = sparql.query().convert()
                bindings = response.get("results", {}).get("bindings", [])
                return [
                    {k: v.get("value") for k, v in binding.items()}
                    for binding in bindings
                ]
            except Exception as err:  # pragma: no cover
                logger.warning("Remote SPARQL failed, falling back to local graph: %s", err)
        return self._query_local_graph(query)

    # ---------- Neo4j payload ----------
    def _labels_for_uri(self, uri: URIRef) -> List[str]:
        parts = str(uri).rstrip('/').split('/')
        label = parts[-1] if parts else "Resource"
        label = label.replace("#", ":")
        return [label or "Resource"]

    def to_neo4j_nodes_and_rels(self) -> Dict[str, list]:
        """Convert triples to Neo4j-friendly payloads with light schema hints."""
        if not self.graph:
            return {"nodes": [], "relationships": []}
        nodes: Dict[str, Dict[str, Any]] = {}
        relationships: List[Dict[str, Any]] = []
        for subj, pred, obj in self.graph:  # type: ignore[assignment]
            subj_id = str(subj)
            obj_id = str(obj)
            # Create/augment subject node
            nodes.setdefault(subj_id, {
                "id": subj_id,
                "labels": self._labels_for_uri(subj),
                "properties": {}
            })
            # Object node if URI
            if isinstance(obj, URIRef):
                nodes.setdefault(obj_id, {
                    "id": obj_id,
                    "labels": self._labels_for_uri(obj),
                    "properties": {},
                })
            # Relationship
            relationships.append({
                "start": subj_id,
                "end": obj_id,
                "type": Path(str(pred)).name or "RELATED_TO",
            })
            # Add human-readable label if available
            if RDFS and pred == RDFS.label and not isinstance(obj, URIRef):
                nodes[subj_id].setdefault("properties", {})["label"] = str(obj)
        return {"nodes": list(nodes.values()), "relationships": relationships}
