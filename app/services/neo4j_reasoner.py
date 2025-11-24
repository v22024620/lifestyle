"""Neo4j GraphRAG helper using official driver."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, List, Sequence

try:
    from neo4j import GraphDatabase  # type: ignore
except ImportError:  # pragma: no cover
    GraphDatabase = None  # type: ignore

from app.services.neo4j_templates import (
    ENTITY_SEARCH,
    PATH_DISCOVERY,
    EVIDENCE_EXTRACTION,
)


@dataclass
class Neo4jConnectionConfig:
    uri: str
    user: str
    password: str


class Neo4jReasoner:
    """Runs entity lookup, path discovery, and evidence collection."""

    def __init__(self, config: Neo4jConnectionConfig):
        self.config = config
        if GraphDatabase:
            self._driver = GraphDatabase.driver(
                config.uri,
                auth=(config.user, config.password),
            )
        else:  # pragma: no cover
            self._driver = None

    def close(self) -> None:
        if self._driver:
            self._driver.close()

    def _run(self, query: str, parameters: Dict[str, Any]) -> List[Dict[str, Any]]:
        if not self._driver:
            return [{"status": "neo4j-driver-missing", "query": query, "parameters": parameters}]
        with self._driver.session() as session:
            result = session.run(query, parameters)
            return [record.data() for record in result]

    def find_entities(self, keywords: Sequence[str], limit: int = 10) -> List[Dict[str, Any]]:
        terms = [kw.lower() for kw in keywords if kw]
        if not terms:
            return []
        return self._run(ENTITY_SEARCH, {"terms": terms, "limit": limit})

    def find_paths(self, start_id: str, end_id: str, max_depth: int = 4, limit: int = 3) -> List[Dict[str, Any]]:
        if not start_id or not end_id:
            return []
        params = {"start_id": start_id, "end_id": end_id, "max_depth": max_depth, "limit": limit}
        return self._run(PATH_DISCOVERY, params)

    def build_evidence(self, studio_id: str, rel_types: Sequence[str] | None = None, limit: int = 25) -> List[Dict[str, Any]]:
        params = {
            "studio_id": studio_id,
            "relationship_types": list(rel_types) if rel_types else None,
            "limit": limit,
        }
        return self._run(EVIDENCE_EXTRACTION, params)

    def run_pipeline(
        self,
        keywords: Sequence[str],
        start_id: str,
        end_id: str,
        studio_id: str,
        rel_types: Sequence[str] | None = None,
    ) -> Dict[str, Any]:
        """Execute entity search + path discovery + evidence collection."""
        entities = self.find_entities(keywords)
        paths = self.find_paths(start_id, end_id)
        evidence = self.build_evidence(studio_id, rel_types)
        return {
            "entities": entities,
            "paths": paths,
            "evidence": evidence,
        }
