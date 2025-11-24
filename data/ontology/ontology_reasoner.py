"""Neo4j helper utilities for ontology experiments."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, List, Optional

from neo4j import Driver, GraphDatabase


@dataclass
class Entity:
    """Simple projection of a Neo4j node."""

    id: int
    labels: List[str]
    props: Dict[str, Any]


@dataclass
class PathEvidence:
    """Container describing a path between two entities."""

    start: Entity
    end: Entity
    relations: List[Dict[str, Any]]


class Neo4jReasoner:
    """Utility class that runs ad-hoc Cypher for GraphRAG style workflows."""

    def __init__(self, uri: str, user: str, password: str) -> None:
        self._driver: Driver = GraphDatabase.driver(uri, auth=(user, password))

    def close(self) -> None:
        self._driver.close()

    # ------------------------------------------------------------------
    # Entity lookup
    # ------------------------------------------------------------------

    @staticmethod
    def _node_to_entity(node) -> Entity:
        return Entity(
            id=node.id,
            labels=list(node.labels),
            props=dict(node.items()),
        )

    @staticmethod
    def _relationship_to_info(rel) -> Dict[str, Any]:
        start_node = rel.start_node
        end_node = rel.end_node
        return {
            "type": rel.type,
            "props": dict(rel.items()),
            "start_labels": list(start_node.labels),
            "start_props": dict(start_node.items()),
            "end_labels": list(end_node.labels),
            "end_props": dict(end_node.items()),
        }

    def _path_to_evidence(self, path) -> PathEvidence:
        nodes = list(path.nodes)
        rels = list(path.relationships)
        start_entity = self._node_to_entity(nodes[0])
        end_entity = self._node_to_entity(nodes[-1])
        rel_infos = [self._relationship_to_info(rel) for rel in rels]
        return PathEvidence(start=start_entity, end=end_entity, relations=rel_infos)

    def find_entities(
        self,
        query: str,
        limit: int = 10,
        label_filter: Optional[List[str]] = None,
    ) -> List[Entity]:
        """Full text style scan over all properties of every node."""

        if label_filter:
            cypher = """
            MATCH (n)
            WHERE ANY(l IN labels(n) WHERE l IN $labels)
              AND ANY(k IN keys(n)
                      WHERE n[k] IS NOT NULL
                        AND toLower(toString(n[k])) CONTAINS toLower($q))
            RETURN n
            LIMIT $limit
            """
        else:
            cypher = """
            MATCH (n)
            WHERE ANY(k IN keys(n)
                      WHERE n[k] IS NOT NULL
                        AND toLower(toString(n[k])) CONTAINS toLower($q))
            RETURN n
            LIMIT $limit
            """

        with self._driver.session() as session:
            result = session.run(
                cypher,
                q=query,
                labels=label_filter or [],
                limit=limit,
            )
            return [self._node_to_entity(rec["n"]) for rec in result]

    # ------------------------------------------------------------------
    # Path exploration
    # ------------------------------------------------------------------

    def find_neighborhood_paths(
        self,
        entity_id: int,
        max_hops: int = 3,
        limit: int = 50,
    ) -> List[PathEvidence]:
        """Find any paths that start from a node and branch out up to N hops."""

        cypher = f"""
        MATCH p = (start)-[r*1..{max_hops}]-(end)
        WHERE id(start) = $start_id
        RETURN p
        LIMIT $limit
        """

        evidences: List[PathEvidence] = []
        with self._driver.session() as session:
            result = session.run(cypher, start_id=entity_id, limit=limit)
            for record in result:
                path = record["p"]
                evidences.append(self._path_to_evidence(path))
        return evidences

    def find_shortest_paths(
        self,
        start_id: int,
        end_id: int,
        max_hops: int = 4,
        limit: int = 5,
    ) -> List[PathEvidence]:
        """Return shortest paths between two specific nodes."""

        cypher = f"""
        MATCH p = shortestPath((s)-[r*1..{max_hops}]-(e))
        WHERE id(s) = $start_id AND id(e) = $end_id
        RETURN p
        LIMIT $limit
        """

        evidences: List[PathEvidence] = []
        with self._driver.session() as session:
            result = session.run(
                cypher,
                start_id=start_id,
                end_id=end_id,
                limit=limit,
            )
            for record in result:
                path = record["p"]
                if path is not None:
                    evidences.append(self._path_to_evidence(path))
        return evidences

    # ------------------------------------------------------------------
    # Formatting helpers
    # ------------------------------------------------------------------

    @staticmethod
    def evidence_to_text(ev: PathEvidence) -> str:
        """Pretty print an evidence bundle so LLM prompts stay compact."""

        def fmt_entity(entity: Entity) -> str:
            label_str = ":".join(entity.labels)
            preferred_name = (
                entity.props.get("name")
                or entity.props.get("rdfs__label")
                or entity.props.get("skos__prefLabel")
                or ""
            )
            return f"[{label_str}] {preferred_name} {entity.props}"

        lines = [f"START {fmt_entity(ev.start)}"]
        for idx, rel in enumerate(ev.relations, start=1):
            target_labels = ":".join(rel["end_labels"])
            lines.append(
                f"  ({idx}) -[{rel['type']} {rel['props']}]-> [{target_labels}] {rel['end_props']}"
            )
        lines.append(f"END {fmt_entity(ev.end)}")
        return "\n".join(lines)
