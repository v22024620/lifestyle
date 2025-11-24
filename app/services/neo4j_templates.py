"""Parameterized Neo4j Cypher templates for GraphRAG."""

ENTITY_SEARCH = """
MATCH (n)
WHERE any(term IN $terms WHERE toLower(coalesce(n.label,'')) CONTAINS term
    OR toLower(coalesce(n.id,'')) CONTAINS term
    OR any(lbl IN labels(n) WHERE toLower(lbl) CONTAINS term))
RETURN n.id AS node_id,
       labels(n) AS labels,
       coalesce(n.label, n.id) AS title,
       coalesce(n.category, n.program, '') AS context,
       n
LIMIT $limit
"""

PATH_DISCOVERY = """
MATCH (start {id:$start_id}), (dest {id:$end_id})
MATCH p = allShortestPaths((start)-[r*1..$max_depth]-(dest))
RETURN [node IN nodes(p) | {id:node.id, labels:labels(node), title:coalesce(node.label,node.id)}] AS nodes,
       [rel IN relationships(p) | {type:type(rel), props:properties(rel)}] AS relationships,
       length(p) AS hops
LIMIT $limit
"""

EVIDENCE_EXTRACTION = """
MATCH (studio {id:$studio_id})-[rel]->(neighbor)
WHERE $relationship_types IS NULL OR type(rel) IN $relationship_types
RETURN studio.id AS studio_id,
       type(rel) AS relationship_type,
       rel AS relationship,
       neighbor.id AS neighbor_id,
       labels(neighbor) AS neighbor_labels,
       coalesce(neighbor.label, neighbor.id) AS neighbor_label
ORDER BY rel.modified DESC NULLS LAST, rel.weight DESC NULLS LAST
LIMIT $limit
"""
