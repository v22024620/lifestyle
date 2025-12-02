# LOP Ontology Pipelines

| Script | 역할 | 주요 옵션 |
| --- | --- | --- |
| `sync_fibo_modules.py` | `fibo-master/` → `data/ontology/raw/` 동기화 | `--module`, `--clean`, `--dry-run` |
| `rdflib_loader.py` | `graphdb_modules.yml` 순서대로 rdflib 로딩/검증 | `--layers`, `--skip-optional`, `--list` |
| `graphdb_seed.py` / `graphdb_seed.sh` | GraphDB `/statements` 로 TTL 업로드 | `--endpoint`, `--repository`, `--validate`, `--dry-run` |
| `neo4j_ingest.py` | n10s `rdf.import.fetch` 기반 Neo4j 적재 | `--skip-wipe`, `--layers`, `--dry-run` |
| `apple_fitness_dataset.py` | (기존) 샘플 TTL 생성 | 선택 |

## 실행 순서
1. **Raw 동기화**: `python data/ontology/pipelines/sync_fibo_modules.py --clean` (필요 모듈만 선택 가능)
2. **로컬 검증**: `python data/ontology/pipelines/rdflib_loader.py --skip-optional`
3. **GraphDB 적재**: `python data/ontology/pipelines/graphdb_seed.py --endpoint http://localhost:7200 --repository lop-dev --validate`
4. **Neo4j 적재**: `python data/ontology/pipelines/neo4j_ingest.py --skip-optional`

> Neo4j 스크립트는 `.env`에 정의된 `LCP_NEO4J_*`를 사용합니다. Git에 비밀번호를 커밋하지 마세요.
