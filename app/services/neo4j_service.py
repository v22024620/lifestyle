"""Neo4j service for graph operations with safe fallback."""
from __future__ import annotations

import logging
from datetime import datetime
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)

try:
    from py2neo import Graph  # type: ignore
except ImportError:  # pragma: no cover - optional dependency
    Graph = None  # type: ignore


class Neo4jService:
    """Handles Neo4j interactions; falls back to stub if driver missing."""

    def __init__(self, uri: str, user: str, password: str):
        self.uri = uri
        self.user = user
        self.password = password
        self._graph: Optional[Graph] = None
        self._last_seeded_at: Optional[str] = None
        self._connect()

    def _connect(self) -> None:
        if not Graph:
            logger.warning("py2neo not installed; Neo4j calls will be stubbed")
            return
        try:
            self._graph = Graph(self.uri, auth=(self.user, self.password))
        except Exception as err:  # pragma: no cover - runtime/connection dependent
            logger.warning("Neo4j connection failed, using stub mode: %s", err)
            self._graph = None

    def run_cypher(self, query: str, parameters: Dict[str, Any] | None = None) -> List[Dict[str, Any]]:
        """Run Cypher query and return records as dict; stub when unavailable."""
        parameters = parameters or {}
        if self._graph:
            try:
                result = self._graph.run(query, parameters)
                return [dict(record) for record in result]  # type: ignore[arg-type]
            except Exception as err:  # pragma: no cover - runtime dependent
                logger.warning("Neo4j query failed, falling back to stub: %s", err)
        return [{"query": query, "parameters": parameters, "mode": "stub"}]

    def is_connected(self) -> bool:
        """Return True if an active Neo4j connection is available."""
        return self._graph is not None

    def load_nodes_and_relationships(self, payload: Dict[str, list]) -> Dict[str, Any]:
        """Ingest nodes/relationships into Neo4j; stubbed when driver missing."""
        nodes = payload.get("nodes", [])
        rels = payload.get("relationships", [])
        if not self._graph:
            return {"status": "stub", "nodes": len(nodes), "relationships": len(rels)}
        created = 0
        try:
            for node in nodes:
                labels = ":".join(node.get("labels", ["Resource"]))
                props = node.get("properties", {})
                node_id = node.get("id")
                self._graph.run(
                    f"MERGE (n:{labels} {{id:$id}}) SET n += $props",
                    {"id": node_id, "props": props},
                )
                created += 1
            for rel in rels:
                self._graph.run(
                    """
                    MATCH (s {id:$start}), (e {id:$end})
                    MERGE (s)-[r:%s]->(e)
                    """ % rel.get("type", "RELATED_TO"),
                    {"start": rel.get("start"), "end": rel.get("end")},
                )
            self._last_seeded_at = datetime.utcnow().isoformat()
            return {"status": "loaded", "nodes": created, "relationships": len(rels)}
        except Exception as err:  # pragma: no cover - runtime dependent
            logger.warning("Failed to load into Neo4j: %s", err)
            return {"status": "error", "error": str(err)}

    def reset(self) -> Dict[str, Any]:
        """Clear stubbed state or drop all nodes in Neo4j for demo purposes."""
        if not self._graph:
            return {"status": "stub-reset"}
        try:
            self._graph.run("MATCH (n) DETACH DELETE n")
            return {"status": "cleared"}
        except Exception as err:  # pragma: no cover
            logger.warning("Failed to reset Neo4j: %s", err)
            return {"status": "error", "error": str(err)}

    def summary(self) -> Dict[str, Any]:
        """Return light-weight stats for dashboards."""
        base: Dict[str, Any] = {"last_seeded_at": self._last_seeded_at}
        if not self._graph:
            base.update({"nodes": 0, "relationships": 0, "mode": "stub"})
            return base
        try:
            node_count = self._graph.run("MATCH (n) RETURN count(n) AS count").evaluate() or 0
            rel_count = self._graph.run("MATCH ()-[r]->() RETURN count(r) AS count").evaluate() or 0
            base.update({"nodes": int(node_count), "relationships": int(rel_count), "mode": "connected"})
        except Exception as err:  # pragma: no cover - runtime dependent
            logger.warning("Failed to collect Neo4j stats: %s", err)
            base.update({"nodes": 0, "relationships": 0, "mode": "error"})
        return base

