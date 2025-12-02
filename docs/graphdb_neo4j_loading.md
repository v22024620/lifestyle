# GraphDB & Neo4j Loading Guide

## 1. 준비
- `.env` 또는 셸 변수에 다음을 설정:
  - `GRAPHDB_ENDPOINT` (예: `http://localhost:7200`)
  - `GRAPHDB_REPOSITORY` (예: `lop-dev`)
  - `LCP_NEO4J_URI`, `LCP_NEO4J_USERNAME`, `LCP_NEO4J_PASSWORD`
- `pip install -r requirements.txt` 로 PyYAML/neo4j/httpx/rdflib 설치

## 2. GraphDB 적재
```bash
python data/ontology/pipelines/graphdb_seed.py \
  --endpoint "${GRAPHDB_ENDPOINT}" \
  --repository "${GRAPHDB_REPOSITORY}" \
  --validate \
  --skip-optional   # datasets layer 제외 시
```
- `--layers metadata lop-core`로 특정 계층만 로딩 가능
- `--dry-run`으로 REST 호출 없이 순서 확인

## 3. Neo4j 적재
```bash
python data/ontology/pipelines/neo4j_ingest.py \
  --skip-optional \
  --skip-wipe      # 필요 시 기존 그래프 유지
```
- 기본값은 `MATCH (n) DETACH DELETE n`으로 그래프를 초기화
- `--dry-run`을 사용하면 `file:///.../lop/LOP-Core.ttl` 목록만 출력

## 4. 검증
- GraphDB Workbench에서 repository를 열고 `SELECT (COUNT(*) AS ?triples) WHERE { ?s ?p ?o }` 실행
- Neo4j에서는 `MATCH (n:owl__Class) RETURN count(n)` 등 기본 질의로 로드 상태 확인

## 5. 문제 해결
- 인증 실패: REST/Neo4j endpoint가 VPN 내부인지 확인
- FIBO 모듈 누락: `python data/ontology/pipelines/sync_fibo_modules.py --module FND-Core` 재실행
- TTL 파싱 에러: Protege에서 `Reasoner > Start reasoner`로 검증 후 수정
\n### Label 전략\n- Neo4j는 n10s prefix 매핑을 통해 lop__ 접두사가 붙은 Label/Relationship을 생성합니다.\n- 여러 프로젝트가 동일 인스턴스를 공유할 때 
eo4j_ingest.py의 PREFIX_MAPPINGS에 프로젝트 prefix를 추가하고 MATCH (n) WHERE any(l IN labels(n) WHERE l STARTS WITH 'lop__') 형태로 질의하면 됩니다.\n
