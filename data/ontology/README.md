# data/ontology (Rebuilt)

이 디렉터리는 Bloomberg FIBO 원본(`fibo-master/`)을 Raw 계층으로 두고, LOP에 특화된 최소 클래스·프로퍼티만을 정의한 `lop/` 레이어를 포함합니다. 기존 TTL은 모두 삭제했으며, 아래 구조를 기준으로 Protege/GraphDB/Neo4j 파이프라인을 다시 구성합니다.

| 폴더 | 설명 |
| --- | --- |
| `lop/` | `LOP-Metadata.ttl`, `LOP-Core.ttl` 등 LOP 커스텀 온톨로지 정의 |
| `pipelines/` | Raw 동기화·검증·GraphDB/Neo4j 적재 스크립트 |
| `datasets/` | 시뮬레이션 TTL (`generate_simulation_data.py` 실행 시 생성) |

## 재구축 절차
1. `python data/ontology/pipelines/sync_fibo_modules.py --clean --module FND-Core ...`로 `data/ontology/raw/` 채우기.
2. Protege에서 `lop/LOP-Metadata.ttl`을 열고 `fibo-master/catalog-v001.xml`을 catalog로 등록.
3. `graphdb_seed.py`, `neo4j_ingest.py`로 `lop` 계층을 적재.
4. `data/simulations/generate_simulation_data.py` 실행으로 `datasets/provider_metrics.ttl`을 생성해 KPI 데이터를 검증.
