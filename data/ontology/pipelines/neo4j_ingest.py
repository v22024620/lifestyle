# data/ontology/pipelines/neo4j_ingest_auto.py
"""
data/ontology 아래에 있는 모든 .ttl 파일을 재귀적으로 찾아서
Neo4j + n10s 로 한 번에 인제스트하는 스크립트.

사용법:
1) .env(LCP_NEO4J_*)에 자격 증명 입력
2) VSCode 터미널에서
     python data/ontology/pipelines/neo4j_ingest_auto.py
"""

from pathlib import Path
from neo4j import GraphDatabase
from data.ontology.pipelines._settings import neo4j_credentials


# 🔧 1) Neo4j 접속 정보 (.env → LCP_NEO4J_*)
NEO4J_URI, NEO4J_USER, NEO4J_PASSWORD = neo4j_credentials()


# 🔧 2) TTL을 찾을 루트 디렉터리
#   이 파일:      .../data/ontology/pipelines/neo4j_ingest_auto.py
#   parent        .../data/ontology/pipelines
#   parent.parent .../data/ontology
ONTOLOGY_DIR = Path(__file__).resolve().parent.parent


def find_ttl_files(root: Path) -> list[Path]:
    """root 이하 모든 .ttl 파일 재귀 탐색."""
    ttl_files = sorted(root.rglob("*.ttl"))
    return ttl_files


def init_graphconfig(session):
    """n10s 그래프 설정 초기화."""
    config = {
        "handleVocabUris": "SHORTEN",
        "handleMultival": "OVERWRITE",
        "typesToLabels": True,
        "keepLangTag": False,
        "preserveOriginalUris": True,
        "keepLangTagShort": False,
    }
    session.run("CALL n10s.graphconfig.init($config)", config=config)


def main():
    print("[INFO] ONTOLOGY_DIR:", ONTOLOGY_DIR)

    ttl_files = find_ttl_files(ONTOLOGY_DIR)
    if not ttl_files:
        print("[ERROR] .ttl 파일을 하나도 찾지 못했습니다.")
        return

    print(f"[INFO] 발견한 TTL 파일 수: {len(ttl_files)}")
    for p in ttl_files:
        print("  -", p)

    driver = GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USER, NEO4J_PASSWORD))

    with driver.session() as session:
        # 0) 기존 그래프 비우기 (원하면 주석 처리 가능)
        print("[INFO] 기존 노드/관계 삭제 중...")
        session.run("MATCH (n) DETACH DELETE n")

        # 1) n10s 설정
        print("[INFO] n10s.graphconfig.init 실행...")
        init_graphconfig(session)

        # 2) 파일 하나씩 import
        total = len(ttl_files)
        for idx, ttl_path in enumerate(ttl_files, start=1):
            file_url = "file:///" + str(ttl_path).replace("\\", "/")
            print(f"[INFO] ({idx}/{total}) Import: {file_url}")
            session.run(
                "CALL n10s.rdf.import.fetch($url, 'Turtle')",
                url=file_url,
            )

    driver.close()
    print("[INFO] Neo4j ingest 자동 처리 완료 ✅")


if __name__ == "__main__":
    main()
