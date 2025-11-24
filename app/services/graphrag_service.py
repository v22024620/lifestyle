"""GraphRAG service combining graph queries, Neo4j and vector search."""
from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Any, Dict, List, Optional

from app.services.vector_service import VectorService
from app.services.ontology_service import OntologyService
from app.services.neo4j_service import Neo4jService

logger = logging.getLogger(__name__)


class GraphRAGService:
    """Creates combined context from graph and vector backends."""

    def __init__(
        self,
        vector_service: VectorService,
        ontology_service: OntologyService,
        neo4j_service: Neo4jService,
        entity_index_path: Optional[str] = None,
    ):
        self.vector_service = vector_service
        self.ontology_service = ontology_service
        self.neo4j_service = neo4j_service
        self.ontology_service.ensure_ready()
        self.entity_index = self._load_entity_index(entity_index_path)

    def _load_entity_index(self, entity_index_path: Optional[str]) -> Dict[str, Dict[str, Any]]:
        path = Path(entity_index_path or "data/ontology/datasets/entity_index.json")
        if not path.exists():
            logger.warning("Entity index not found at %s", path)
            return {}
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
            return {entry.get("iri"): entry for entry in data.get("entities", []) if entry.get("iri")}
        except Exception as err:  # pragma: no cover - file corruption
            logger.warning("Failed to load entity index: %s", err)
            return {}

    def _label_for(self, iri: Optional[str]) -> Optional[str]:
        if not iri:
            return None
        entry = self.entity_index.get(iri)
        return entry.get("label") if entry else None

    def build_context(self, user_query: str | None, studio_id: str) -> Dict[str, Any]:
        """Return merged context package for downstream agents with simple scoring."""
        query_text = user_query or "studio insight"

        # GraphDB / rdflib view
        sparql = f"""
        PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
        SELECT ?s ?p ?o WHERE {{
          ?s ?p ?o .
          FILTER(CONTAINS(STR(?s), "{studio_id}"))
        }} LIMIT 50
        """
        graph_context = self.ontology_service.sparql_query(sparql)

        # Vector search anchored by studio filter
        vector_context = self.vector_service.search(
            query_text,
            metadata_filter={"studio_id": studio_id},
        )

        # Neo4j context
        cypher = """
        MATCH (m {id:$studio_id})-[r]-(n)
        RETURN m as studio, TYPE(r) as rel_type, n as neighbor LIMIT 50
        """
        neo4j_context = self.neo4j_service.run_cypher(cypher, {"studio_id": studio_id})

        merged = self.ontology_service.merge_graphs()
        # Simple combined score for ordering or debugging
        combined_score = len(graph_context) * 0.1 + len(vector_context) * 0.2 + len(neo4j_context) * 0.1

        return {
            "graph": graph_context,
            "vector": vector_context,
            "neo4j": neo4j_context,
            "meta": {"studio_id": studio_id, "query": query_text, "combined_score": round(combined_score, 2)},
            "graph_meta": merged,
        }

    def seed_neo4j_from_ontology(self) -> Dict[str, Any]:
        """Load ontology-derived nodes/relationships into Neo4j."""
        payload = self.ontology_service.to_neo4j_nodes_and_rels()
        return self.neo4j_service.load_nodes_and_relationships(payload)

    def build_reasoned_evidence(self, user_query: str | None, studio_id: str) -> Dict[str, Any]:
        """Combine vector/graph/Neo4j 결과를 증거 구조로 가공."""
        context_bundle = self.build_context(user_query, studio_id)
        evidence_items: List[Dict[str, Any]] = []

        for triple in context_bundle.get("graph", []):
            subj = triple.get("s")
            evidence_items.append({
                "source": "graph",
                "subject": subj,
                "predicate": triple.get("p"),
                "object": triple.get("o"),
                "label": self._label_for(subj),
                "confidence": 0.6,
            })

        for doc in context_bundle.get("vector", []):
            metadata = doc.get("metadata", {})
            subject = metadata.get("studio_id", studio_id)
            evidence_items.append({
                "source": "vector",
                "subject": subject,
                "predicate": "text-match",
                "object": doc.get("content"),
                "score": doc.get("score"),
                "label": self._label_for(subject if isinstance(subject, str) else None),
                "confidence": 0.7,
            })

        for rel in context_bundle.get("neo4j", []):
            subject = None
            neighbor = rel.get("neighbor")
            studio_node = rel.get("studio")
            if isinstance(studio_node, dict):
                subject = studio_node.get("id")
            elif isinstance(studio_node, str):
                subject = studio_node
            elif isinstance(rel, dict) and "parameters" in rel:
                subject = rel["parameters"].get("studio_id")
            evidence_items.append({
                "source": "neo4j",
                "subject": subject,
                "predicate": rel.get("rel_type", rel.get("mode", "related")),
                "object": neighbor,
                "label": self._label_for(subject if isinstance(subject, str) else None),
                "confidence": 0.8,
            })

        summary = {
            "total_evidence": len(evidence_items),
            "by_source": {
                "graph": len([e for e in evidence_items if e["source"] == "graph"]),
                "vector": len([e for e in evidence_items if e["source"] == "vector"]),
                "neo4j": len([e for e in evidence_items if e["source"] == "neo4j"]),
            },
        }

        context_bundle["evidence"] = {"items": evidence_items, "summary": summary}
        return context_bundle
