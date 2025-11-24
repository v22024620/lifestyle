# data/ontology/pipelines/neo4j_ingest.py

from pathlib import Path
from neo4j import GraphDatabase
from data.ontology.pipelines._settings import neo4j_credentials

# 🔧 접속 정보는 .env(LCP_NEO4J_*)로부터 자동 로드됩니다.
NEO4J_URI, NEO4J_USER, NEO4J_PASSWORD = neo4j_credentials()

CYPHER_PATH = Path(__file__).parent / "neo4j_ingest.cypher"


def load_statements(path: Path) -> list[str]:
    """cypher 파일을 읽어서 ; 기준으로 문장 분리."""
    text = path.read_text(encoding="utf-8")

    # 윈도우 개행 정리
    text = text.replace("\r\n", "\n")

    # cypher-shell 전용 명령(:use, :begin 같은 것) 제거
    cleaned_lines = []
    for line in text.splitlines():
        striped = line.strip()
        if striped.startswith(":"):
            # :use neo4j, :begin, :commit 같은 건 neo4j 드라이버에서 안 먹으니까 제거
            continue
        cleaned_lines.append(line)
    cleaned = "\n".join(cleaned_lines)

    # ; 기준으로 쿼리 나누기
    stmts = [s.strip() for s in cleaned.split(";") if s.strip()]
    return stmts


def run_script():
    if not CYPHER_PATH.exists():
        raise FileNotFoundError(f"Cypher 파일을 찾을 수 없습니다: {CYPHER_PATH}")

    statements = load_statements(CYPHER_PATH)
    print(f"[INFO] {len(statements)}개의 Cypher 문장을 실행합니다.")

    driver = GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USER, NEO4J_PASSWORD))

    with driver.session() as session:
        for idx, stmt in enumerate(statements, start=1):
            print(f"[INFO] ({idx}/{len(statements)}) 실행 중...")
            session.run(stmt)

    driver.close()
    print("[INFO] Neo4j ingest 완료 ✅")


if __name__ == "__main__":
    run_script()

