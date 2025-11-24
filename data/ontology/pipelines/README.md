# LOP Ontology Pipelines

| 스크립트 | 설명 | 필요 환경변수 |
| --- | --- | --- |
| `rdflib_loader.py` | 로컬 rdflib 그래프로 TTL 검사/머지 | 없음 (python 실행) |
| `graphdb_seed.sh` | GraphDB REST `/statements` 로 TTL 순차 업로드 | `GRAPHDB_ENDPOINT`, `GRAPHDB_REPOSITORY` |
| `neo4j_ingest.cypher` | Neo4j n10s RDF import | `.env`(`LCP_NEO4J_*`) + `basePath` 파라미터(Cypher) |
| `apple_fitness_dataset.py` | 애플 피트니스 온톨로지 샘플 TTL 생성 | 선택 (python 실행) |
| `seed_real_graphs.py` | GraphDB+Neo4j 전체 모듈/데이터 일괄 로드 | `.env`(`LCP_NEO4J_*`, `graphdb_endpoint`) |

> 모든 Neo4j 관련 스크립트는 레포 루트의 `.env` (예: `LCP_NEO4J_PASSWORD`)를 통해 자격 증명을 읽습니다. Git에는 올리지 마세요.

## 실행 순서
1. `python data/ontology/pipelines/rdflib_loader.py`
2. `bash data/ontology/pipelines/graphdb_seed.sh`
3. `cypher-shell -u neo4j -p pass -f data/ontology/pipelines/neo4j_ingest.cypher --param basePath="file:///.../data/ontology"`
각 스크립트는 로그를 출력하며 누락된 파일을 경고합니다.
- `ontology_reasoner.py` | Neo4j Reasoner (legacy ontology helper) | optional (uses bolt credentials)

