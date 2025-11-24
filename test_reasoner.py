"""Quick smoke test for the ontology Neo4jReasoner."""

from app.config import get_settings
from data.ontology.ontology_reasoner import Neo4jReasoner


def _require_settings():
    settings = get_settings()
    if not settings.neo4j_password:
        raise RuntimeError("Set LCP_NEO4J_PASSWORD in .env before running test_reasoner.py")
    return settings


def main() -> None:
    settings = _require_settings()
    reasoner = Neo4jReasoner(
        uri=settings.neo4j_uri,
        user=settings.neo4j_user,
        password=settings.neo4j_password,
    )

    print("=== Entity search ===")
    entities = reasoner.find_entities("test", limit=5)
    for entity in entities:
        print(f"id={entity.id}, labels={entity.labels}, props={entity.props}")

    reasoner.close()


if __name__ == "__main__":
    main()
