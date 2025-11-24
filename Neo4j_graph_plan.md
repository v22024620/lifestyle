# Neo4j GraphRAG 파이프라인 기획 (LOP 기획자 관점)

1. **엔티티 탐색** – 스튜디오, 프로그램, 계약, KPI 등 그래프 노드를 키워드로 탐색해 사용자의 질의에 맞는 후보를 빠르게 제시한다. (`ENTITY_SEARCH`)
2. **경로 탐색** – 공급자와 운영자 노드를 연결하는 최단 경로/영향 경로를 찾아 계약·리스크 흐름을 시각화한다. (`PATH_DISCOVERY`)
3. **증거 수집** – 특정 스튜디오와 주변 노드의 관계를 읽어 KPI 변화 근거, 리스크 이벤트, 권장 조치를 Evidence 구조로 만든다. (`EVIDENCE_EXTRACTION`)
4. **엔드투엔드 파이프라인** – `Neo4jReasoner.run_pipeline()`이 위 세 단계를 순차 실행해 GraphRAG에 필요한 엔티티 목록, 경로, 증거 패키지를 반환한다.
5. **LOP 적용 예시**
   - 공급자: “SGANG01”과 “Program X” 연결 경로 추적 → 환불 이벤트 근거 도출.
   - 운영자: 글로벌 KPI 하락 시 `find_entities`로 원인 후보를 조합하고 `build_evidence`로 증빙 확보.
   - 고객: 특정 회원 세그먼트(하이리스크)와 관련된 그래프 증거를 추출해 Explainer Agent가 설명.

```python
from app.config import get_settings
from app.services.neo4j_reasoner import Neo4jReasoner, Neo4jConnectionConfig

settings = get_settings()
config = Neo4jConnectionConfig(
    uri=settings.neo4j_uri,
    user=settings.neo4j_user,
    password=settings.neo4j_password,
)
reasoner = Neo4jReasoner(config)
result = reasoner.run_pipeline([
    "Studio",
    "Settlement"
], start_id="SGANG01", end_id="LOPFitnessDivision", studio_id="SGANG01")
print(result)
reasoner.close()
```
